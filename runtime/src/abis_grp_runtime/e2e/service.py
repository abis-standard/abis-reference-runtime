"""Reference runtime E2E integration service — multi-vertical, no outcome evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from abis_grp_runtime.agent.adapter import ExternalAgentAdapter
from abis_grp_runtime.agent.envelope import AgentRequestEnvelope, AgentResponseEnvelope
from abis_grp_runtime.agent.serialization import request_from_dict
from abis_grp_runtime.core import RuntimeCore
from abis_grp_runtime.registry.interaction_registry import RuntimeInteractionRegistry


def extract_native_external_identifier(agent_response: AgentResponseEnvelope) -> str | None:
    native = agent_response.native_result
    if not native:
        return None
    identifier = native.get("external_identifier")
    return str(identifier) if identifier else None


def extract_crs_native_result(agent_response: AgentResponseEnvelope) -> dict[str, Any] | None:
    native = agent_response.native_result
    if not native:
        return None
    payload = native.get("payload") or {}
    crs = payload.get("crs_native_result")
    if isinstance(crs, dict):
        return crs
    return None


@dataclass(frozen=True)
class GrokE2EResponse:
    """Full E2E response — native result and execution trace only (no outcome evaluation)."""

    agent_response: AgentResponseEnvelope
    native_external_identifier: str | None = None
    reservation_id: str | None = None
    crs_native_result: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        base = self.agent_response.to_dict()
        base["native_external_identifier"] = self.native_external_identifier
        base["reservation_id"] = self.reservation_id or self.native_external_identifier
        base["crs_native_result"] = self.crs_native_result
        return base


class GrokE2EService:
    """
    LEGACY_INTERNAL_NAME: GrokE2EService
    PUBLIC_SEMANTICS: provider-neutral reference runtime integration service.

    Routes Agent Contract → Runtime Core → Adapter Connector → controlled simulator.
    Does not perform normative ABIS Business Outcome evaluation.
    """

    def __init__(self, registry: RuntimeInteractionRegistry) -> None:
        self._registry = registry

    @property
    def registry(self) -> RuntimeInteractionRegistry:
        return self._registry

    def invoke(self, request: AgentRequestEnvelope) -> GrokE2EResponse:
        vertical = str(request.metadata.get("vertical") or "").strip().lower()
        if not vertical:
            raise ValueError("vertical missing from request metadata")
        operation = request.operation.strip().lower()
        adapter = self._registry.get_adapter(vertical, operation)
        connector = adapter.get_connector()
        bound_operation = adapter.bind_operation(operation)
        runtime = RuntimeCore(connector=connector)
        adapter_client = ExternalAgentAdapter(runtime)
        agent_response = adapter_client.invoke(request)
        crs_native = extract_crs_native_result(agent_response)
        native_id = extract_native_external_identifier(agent_response)
        reservation_id = crs_native.get("reservation_id") if crs_native is not None else None
        return GrokE2EResponse(
            agent_response=agent_response,
            native_external_identifier=native_id,
            reservation_id=reservation_id or native_id,
            crs_native_result=crs_native,
        )

    def invoke_from_dict(self, payload: Mapping[str, Any]) -> GrokE2EResponse:
        data = dict(payload)
        if "structured_input" not in data and "input" in data:
            data["structured_input"] = dict(data.pop("input"))
        if "authorization_token" not in data:
            data["authorization_token"] = "ALLOW"
        if "execution_class" not in data:
            data["execution_class"] = "CONTROLLED_SIMULATOR"
        vertical = str(data.get("vertical") or "").strip().lower()
        if not vertical:
            raise ValueError("vertical missing from invoke payload")
        metadata = dict(data.get("metadata") or {})
        metadata["vertical"] = vertical
        data["metadata"] = metadata
        request = request_from_dict(data)
        return self.invoke(request)
