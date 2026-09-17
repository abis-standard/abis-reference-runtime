"""Technical native observation — implementation surface only (not ABIS Interaction invoke)."""

from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

from abis_grp_runtime.agent.continuity_reference import ICR_FIELD_NAME, validate_icr
from abis_grp_runtime.agent.envelope import AgentIdentity, AgentResponseEnvelope
from abis_grp_runtime.agent.execution_provenance import build_execution_provenance
from abis_grp_runtime.authorization import AuthorizationInput, evaluate_authorization
from abis_grp_runtime.evidence import FoundationTrace
from abis_grp_runtime.execution import ExecutionClass, resolve_execution_disposition
from abis_grp_runtime.gateway.errors import GatewayError, GatewayErrorCode
from abis_grp_runtime.native_result import NativeResultEnvelope
from abis_grp_runtime.outcome import NullOutcomeInterpreter
from abis_grp_runtime.semantic import InteractionEnvelope, SemanticBoundaryInput, SemanticReference

OBSERVE_OPERATION = "observe"
OBSERVE_SUPPORTED_VERTICALS = frozenset({"restaurant"})

ALLOWED_OBSERVE_KEYS = frozenset(
    {
        "correlation_id",
        "external_identifier",
        ICR_FIELD_NAME,
    }
)

URL_PATTERN = re.compile(r"(?i)(https?://|file://|ftp://|\\\\)")


def _native_result_to_dict(result: NativeResultEnvelope | None) -> dict[str, Any] | None:
    if result is None:
        return None
    return {
        "technical_status": result.technical_status,
        "external_status": result.external_status,
        "external_identifier": result.external_identifier,
        "payload": dict(result.payload),
        "error": dict(result.error) if result.error else None,
        "timing_ms": result.timing_ms,
        "source": result.source,
    }


def validate_observe_payload(data: Any, *, vertical: str) -> tuple[dict[str, Any] | None, GatewayError | None]:
    vertical_norm = vertical.strip().lower()
    if vertical_norm not in OBSERVE_SUPPORTED_VERTICALS:
        return None, GatewayError(
            GatewayErrorCode.REQUEST_INVALID,
            "observe not supported for vertical",
            http_status=403,
            detail={"vertical": vertical_norm, "supported": sorted(OBSERVE_SUPPORTED_VERTICALS)},
        )

    if not isinstance(data, dict):
        return None, GatewayError(GatewayErrorCode.REQUEST_INVALID, "JSON object required", http_status=400)

    unknown = sorted(set(data.keys()) - ALLOWED_OBSERVE_KEYS)
    if unknown:
        return None, GatewayError(
            GatewayErrorCode.REQUEST_INVALID,
            "unsupported observe fields",
            http_status=400,
            detail={"fields": unknown},
        )

    for value in data.values():
        if isinstance(value, str) and URL_PATTERN.search(value):
            return None, GatewayError(
                GatewayErrorCode.REQUEST_INVALID,
                "URL-like values are not permitted",
                http_status=400,
            )

    correlation_id = str(data.get("correlation_id") or "").strip()
    external_identifier = str(data.get("external_identifier") or "").strip()
    if not correlation_id:
        return None, GatewayError(
            GatewayErrorCode.REQUEST_INVALID,
            "correlation_id is required",
            http_status=400,
            detail={"missing": ["correlation_id"]},
        )
    if not external_identifier:
        return None, GatewayError(
            GatewayErrorCode.REQUEST_INVALID,
            "external_identifier is required",
            http_status=400,
            detail={"missing": ["external_identifier"]},
        )

    icr_raw = data.get(ICR_FIELD_NAME)
    icr_value = str(icr_raw).strip() if icr_raw is not None else None
    if icr_value:
        icr_error = validate_icr(
            icr_value,
            forbidden_equals=(external_identifier, correlation_id),
        )
        if icr_error:
            return None, GatewayError(GatewayErrorCode.REQUEST_INVALID, icr_error, http_status=400)

    normalized = {
        "vertical": vertical_norm,
        "correlation_id": correlation_id,
        "external_identifier": external_identifier,
    }
    if icr_value:
        normalized[ICR_FIELD_NAME] = icr_value
    return normalized, None


def execute_observe(
    service: Any,
    *,
    normalized: dict[str, Any],
    authorization_token: str,
) -> AgentResponseEnvelope:
    """Perform technical/native observation — NOT Business Outcome Evaluation."""
    vertical = normalized["vertical"]
    correlation_id = normalized["correlation_id"]
    external_identifier = normalized["external_identifier"]
    implementation_continuity_reference = normalized.get(ICR_FIELD_NAME)
    request_id = str(uuid4())

    trace = FoundationTrace(correlation_id=correlation_id, request_id=request_id)
    trace.record("observation", "START", external_identifier=external_identifier)

    authorization = evaluate_authorization(AuthorizationInput(permission_token=authorization_token))
    trace.record("authorization", authorization.state.value, reason=authorization.reason)
    if not authorization.allowed:
        trace.record("observation", "REJECTED", reason=authorization.reason)
        return AgentResponseEnvelope(
            request_id=request_id,
            correlation_id=correlation_id,
            implementation_continuity_reference=implementation_continuity_reference,
            transport_status="REJECTED",
            agent_identity=AgentIdentity(agent_id="technical-observer", agent_type="observe-client"),
            authorization_disposition={
                "state": authorization.state.value,
                "reason": authorization.reason,
            },
            execution_disposition={
                "execution_class": ExecutionClass.CONTROLLED_SIMULATOR.value,
                "policy": "DENY",
                "reason": authorization.reason,
            },
            native_result=None,
            outcome_disposition={"disposition": "NOT_EVALUATED", "reason": "observation rejected"},
            execution_provenance=None,
            trace_reference=trace.to_dict(),
        )

    execution = resolve_execution_disposition(ExecutionClass.CONTROLLED_SIMULATOR)
    trace.record("execution_disposition", execution.policy.value)

    adapter = service.registry.get_adapter(vertical, "reserve")
    connector = adapter.get_connector()
    native = connector.execute(
        OBSERVE_OPERATION,
        {"external_identifier": external_identifier},
    )
    trace.record("native_observation", "COMPLETE", external_status=native.external_status)

    semantic_placeholder = SemanticBoundaryInput(
        participant_ref=SemanticReference("implementation_participant", f"observe-participant-{correlation_id}"),
        intent_ref=SemanticReference("implementation_intent", f"observe-intent-{correlation_id}"),
        interaction=InteractionEnvelope(
            interaction_ref=SemanticReference("implementation_interaction", f"observe-{correlation_id}"),
            capability_ref=SemanticReference("implementation_capability", f"observe-capability-{correlation_id}"),
            decision_ref=SemanticReference("implementation_decision", f"observe-decision-{correlation_id}"),
        ),
        metadata={"observation": True},
    )
    outcome = NullOutcomeInterpreter().interpret(
        semantic_input=semantic_placeholder,
        native_result=native,
    )
    trace.record("outcome_interpreter", outcome.disposition, reason=outcome.reason)

    provenance = build_execution_provenance(
        vertical=vertical,
        operation=OBSERVE_OPERATION,
        business_system_identifier=adapter.business_system_identifier,
        business_system_classification=adapter.business_system_classification,
        implementation_continuity_reference=implementation_continuity_reference,
        observation_kind="native_technical_observation",
    )

    transport_status = "ACCEPTED"
    if native.payload.get("crs_native_result", {}).get("error") == "NOT_FOUND":
        transport_status = "REJECTED"

    return AgentResponseEnvelope(
        request_id=request_id,
        correlation_id=correlation_id,
        implementation_continuity_reference=implementation_continuity_reference,
        transport_status=transport_status,
        agent_identity=AgentIdentity(agent_id="technical-observer", agent_type="observe-client"),
        authorization_disposition={
            "state": authorization.state.value,
            "reason": authorization.reason,
        },
        execution_disposition={
            "execution_class": execution.execution_class.value,
            "policy": execution.policy.value,
            "reason": "technical native observation",
        },
        native_result=_native_result_to_dict(native),
        outcome_disposition={
            "disposition": outcome.disposition,
            "reason": outcome.reason,
            "outcome_ref": outcome.outcome_ref,
        },
        execution_provenance=provenance,
        trace_reference=trace.to_dict(),
    )
