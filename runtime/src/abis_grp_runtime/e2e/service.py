"""Reference runtime E2E integration service — controlled vertical, no outcome evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from abis_grp_runtime.agent.adapter import ExternalAgentAdapter
from abis_grp_runtime.agent.envelope import AgentRequestEnvelope, AgentResponseEnvelope
from abis_grp_runtime.agent.serialization import request_from_dict
from abis_grp_runtime.connectors.restaurant_simulator import RestaurantSimulatorConnector
from abis_grp_runtime.core import RuntimeCore


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
    reservation_id: str | None = None
    crs_native_result: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        base = self.agent_response.to_dict()
        base["reservation_id"] = self.reservation_id
        base["crs_native_result"] = self.crs_native_result
        return base


class GrokE2EService:
    """
    LEGACY_INTERNAL_NAME: GrokE2EService
    PUBLIC_SEMANTICS: provider-neutral reference runtime integration service.

    Connects Agent Contract → Runtime Core → Restaurant Connector → CRS.
    Does not perform normative ABIS Business Outcome evaluation.
    """

    def __init__(self, crs_engine: Any) -> None:
        connector = RestaurantSimulatorConnector(crs_engine)
        runtime = RuntimeCore(connector=connector)
        self._adapter = ExternalAgentAdapter(runtime)

    def invoke(self, request: AgentRequestEnvelope) -> GrokE2EResponse:
        agent_response = self._adapter.invoke(request)
        crs_native = extract_crs_native_result(agent_response)
        reservation_id = crs_native.get("reservation_id") if crs_native is not None else None
        return GrokE2EResponse(
            agent_response=agent_response,
            reservation_id=reservation_id,
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
        request = request_from_dict(data)
        return self.invoke(request)
