"""External Agent → Runtime Core invocation adapter."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from abis_grp_runtime.agent.continuity_reference import generate_icr, validate_icr
from abis_grp_runtime.agent.envelope import AgentRequestEnvelope, AgentResponseEnvelope
from abis_grp_runtime.agent.errors import AgentContractErrorCode, AgentErrorEnvelope
from abis_grp_runtime.agent.validation import validate_agent_request
from abis_grp_runtime.authorization import AuthorizationInput
from abis_grp_runtime.context import RuntimeRequestContext
from abis_grp_runtime.core import RuntimeCore, RuntimePipelineResult
from abis_grp_runtime.execution import ExecutionClass, resolve_execution_disposition
from abis_grp_runtime.native_result import NativeResultEnvelope
from abis_grp_runtime.semantic import InteractionEnvelope, SemanticBoundaryInput, SemanticReference


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


def _build_semantic_input(request: AgentRequestEnvelope, correlation_id: str) -> SemanticBoundaryInput:
    """Build implementation representations from opaque request references."""
    refs = dict(request.structured_input.get("semantic_refs") or {})
    participant_id = str(refs.get("participant_id") or f"impl-participant-{correlation_id}")
    intent_id = str(refs.get("intent_id") or f"impl-intent-{correlation_id}")
    interaction_id = str(refs.get("interaction_id") or f"impl-interaction-{correlation_id}")
    return SemanticBoundaryInput(
        participant_ref=SemanticReference("implementation_participant", participant_id),
        intent_ref=SemanticReference("implementation_intent", intent_id),
        interaction=InteractionEnvelope(
            interaction_ref=SemanticReference("implementation_interaction", interaction_id),
            capability_ref=SemanticReference(
                "implementation_capability",
                str(refs.get("capability_id") or f"impl-capability-{correlation_id}"),
            ),
            decision_ref=SemanticReference(
                "implementation_decision",
                str(refs.get("decision_id") or f"impl-decision-{correlation_id}"),
            ),
        ),
        metadata={"agent_id": request.agent_id, "agent_type": request.agent_type},
    )


def _error_response(
    request: AgentRequestEnvelope,
    *,
    request_id: str,
    correlation_id: str,
    transport_status: str,
    error: AgentErrorEnvelope,
    authorization: dict[str, Any] | None = None,
    execution: dict[str, Any] | None = None,
) -> AgentResponseEnvelope:
    return AgentResponseEnvelope(
        request_id=request_id,
        correlation_id=correlation_id,
        transport_status=transport_status,
        agent_identity=request.identity,
        authorization_disposition=authorization
        or {"state": "UNKNOWN", "reason": error.message},
        execution_disposition=execution
        or {
            "execution_class": request.execution_class,
            "policy": "DENY",
            "reason": error.message,
        },
        native_result=None,
        outcome_disposition=None,
        execution_provenance=None,
        trace_reference={"correlation_id": correlation_id, "request_id": request_id},
        error=error,
    )


class ExternalAgentAdapter:
    """
    Agent-neutral entry boundary.

    Provider-specific clients (Grok, ChatGPT, Claude, etc.) wrap this contract.
    Runtime Core remains provider-agnostic.
    """

    def __init__(self, runtime: RuntimeCore | None = None) -> None:
        self._runtime = runtime or RuntimeCore()

    def invoke(
        self,
        request: AgentRequestEnvelope,
        *,
        execution_provenance: dict[str, Any] | None = None,
    ) -> AgentResponseEnvelope:
        request_id = request.request_id or str(uuid4())
        correlation_id = request.correlation_id or str(uuid4())
        structured = dict(request.structured_input)
        idempotency_key = str(structured.get("idempotency_key") or "")
        external_identifier = str(structured.get("external_identifier") or "")

        icr_error = validate_icr(
            request.implementation_continuity_reference,
            forbidden_equals=(
                idempotency_key or None,
                external_identifier or None,
                correlation_id,
                request_id,
            ),
        )
        if icr_error is not None:
            return _error_response(
                request,
                request_id=request_id,
                correlation_id=correlation_id,
                transport_status="REJECTED",
                error=AgentErrorEnvelope(
                    code=AgentContractErrorCode.INVALID_REQUEST,
                    message=icr_error,
                ),
            )

        implementation_continuity_reference = request.implementation_continuity_reference
        if not implementation_continuity_reference or not str(implementation_continuity_reference).strip():
            implementation_continuity_reference = generate_icr()

        validation_error = validate_agent_request(request)
        if validation_error is not None:
            return _error_response(
                request,
                request_id=request_id,
                correlation_id=correlation_id,
                transport_status="REJECTED",
                error=validation_error,
            )

        execution_class = ExecutionClass.parse(request.execution_class)
        execution_preview = resolve_execution_disposition(execution_class)
        if not execution_preview.allowed:
            return _error_response(
                request,
                request_id=request_id,
                correlation_id=correlation_id,
                transport_status="REJECTED",
                error=AgentErrorEnvelope(
                    code=AgentContractErrorCode.EXECUTION_CLASS_DENIED,
                    message=execution_preview.reason,
                    detail={"execution_class": execution_class.value},
                ),
                execution={
                    "execution_class": execution_class.value,
                    "policy": execution_preview.policy.value,
                    "reason": execution_preview.reason,
                },
            )

        context = RuntimeRequestContext.create(
            agent_id=request.agent_id,
            execution_class=execution_class,
            correlation_id=correlation_id,
            request_id=request_id,
            trace_context={"agent_type": request.agent_type},
        )
        semantic_input = _build_semantic_input(request, correlation_id)
        auth_input = AuthorizationInput(permission_token=request.authorization_token)

        try:
            pipeline: RuntimePipelineResult = self._runtime.process(
                context,
                semantic_input,
                auth_input,
                operation=request.operation,
                operation_context=dict(request.structured_input),
            )
        except Exception as exc:  # pragma: no cover - defensive boundary
            return _error_response(
                request,
                request_id=request_id,
                correlation_id=correlation_id,
                transport_status="ERROR",
                error=AgentErrorEnvelope(
                    code=AgentContractErrorCode.RUNTIME_ERROR,
                    message=str(exc),
                ),
            )

        if not pipeline.authorization.allowed:
            return _error_response(
                request,
                request_id=request_id,
                correlation_id=correlation_id,
                transport_status="REJECTED",
                error=AgentErrorEnvelope(
                    code=AgentContractErrorCode.UNAUTHORIZED,
                    message=pipeline.authorization.reason,
                ),
                authorization={
                    "state": pipeline.authorization.state.value,
                    "reason": pipeline.authorization.reason,
                },
                execution={
                    "execution_class": pipeline.execution.execution_class.value,
                    "policy": pipeline.execution.policy.value,
                    "reason": pipeline.execution.reason,
                },
            )

        if pipeline.halted and not pipeline.control_plane_pass:
            code = (
                AgentContractErrorCode.EXECUTION_CLASS_DENIED
                if not pipeline.execution.allowed
                else AgentContractErrorCode.RUNTIME_ERROR
            )
            return _error_response(
                request,
                request_id=request_id,
                correlation_id=correlation_id,
                transport_status="REJECTED",
                error=AgentErrorEnvelope(
                    code=code,
                    message=pipeline.halt_reason or "runtime halted",
                ),
                authorization={
                    "state": pipeline.authorization.state.value,
                    "reason": pipeline.authorization.reason,
                },
                execution={
                    "execution_class": pipeline.execution.execution_class.value,
                    "policy": pipeline.execution.policy.value,
                    "reason": pipeline.execution.reason,
                },
            )

        outcome_dict = None
        if pipeline.outcome_disposition is not None:
            outcome_dict = {
                "disposition": pipeline.outcome_disposition.disposition,
                "reason": pipeline.outcome_disposition.reason,
                "outcome_ref": pipeline.outcome_disposition.outcome_ref,
            }

        provenance = execution_provenance
        if provenance is not None and implementation_continuity_reference:
            provenance = dict(provenance)
            provenance["implementation_continuity_reference"] = implementation_continuity_reference
            provenance["implementation_continuity_disclaimer"] = (
                "implementation correlation only — not ABIS Interaction identity"
            )

        return AgentResponseEnvelope(
            request_id=request_id,
            correlation_id=correlation_id,
            implementation_continuity_reference=implementation_continuity_reference,
            transport_status="ACCEPTED",
            agent_identity=request.identity,
            authorization_disposition={
                "state": pipeline.authorization.state.value,
                "reason": pipeline.authorization.reason,
            },
            execution_disposition={
                "execution_class": pipeline.execution.execution_class.value,
                "policy": pipeline.execution.policy.value,
                "reason": pipeline.execution.reason,
            },
            native_result=_native_result_to_dict(pipeline.native_result),
            outcome_disposition=outcome_dict,
            execution_provenance=provenance,
            trace_reference=pipeline.trace.to_dict(),
        )
