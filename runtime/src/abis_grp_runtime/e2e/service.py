"""Grok E2E integration service — full controlled vertical."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Mapping

from abis_grp_runtime.agent.adapter import ExternalAgentAdapter
from abis_grp_runtime.agent.envelope import AgentRequestEnvelope, AgentResponseEnvelope
from abis_grp_runtime.agent.serialization import request_from_dict
from abis_grp_runtime.connectors.restaurant_simulator import RestaurantSimulatorConnector
from abis_grp_runtime.core import RuntimeCore
from abis_grp_runtime.outcome_testbed import ExpectedState, OutcomeResultPatternTestbed


def expected_state_from_request(request: AgentRequestEnvelope) -> ExpectedState:
    data = dict(request.structured_input)
    party_size = data.get("party_size")
    return ExpectedState(
        date=data.get("date"),
        time=data.get("time"),
        party_size=int(party_size) if party_size is not None else None,
        seating_type=data.get("seating_type"),
        status=data.get("expected_status"),
    )


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
    """Full E2E response — layers kept distinct for External Agent consumption."""

    agent_response: AgentResponseEnvelope
    outcome_evaluation: dict[str, Any]
    evidence_trace: dict[str, Any]
    reservation_id: str | None = None
    crs_native_result: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        base = self.agent_response.to_dict()
        base["outcome_evaluation"] = self.outcome_evaluation
        base["evidence_trace"] = self.evidence_trace
        base["reservation_id"] = self.reservation_id
        base["crs_native_result"] = self.crs_native_result
        return base


class GrokE2EService:
    """
    Connects M-202 Agent Contract → M-201 Runtime → Restaurant Connector → CRS → M-204 Testbed.
    """

    def __init__(self, crs_engine: Any) -> None:
        connector = RestaurantSimulatorConnector(crs_engine)
        runtime = RuntimeCore(connector=connector)
        self._adapter = ExternalAgentAdapter(runtime)
        self._testbed = OutcomeResultPatternTestbed()

    def invoke(self, request: AgentRequestEnvelope) -> GrokE2EResponse:
        agent_response = self._adapter.invoke(request)
        crs_native = extract_crs_native_result(agent_response)

        outcome_evaluation: dict[str, Any] | None = None
        evidence_trace: dict[str, Any] | None = None
        reservation_id = None

        if crs_native is not None:
            reservation_id = crs_native.get("reservation_id")
            eval_native = copy.deepcopy(crs_native)
            # TEST ONLY: optional label override for negative E2E verification
            if request.structured_input.get("_test_reason_override") is not None:
                eval_native["reason"] = request.structured_input["_test_reason_override"]
            if request.structured_input.get("_test_scenario_override") is not None:
                eval_native["test_scenario"] = request.structured_input["_test_scenario_override"]

            expected = expected_state_from_request(request)
            comparison, trace = self._testbed.evaluate(
                expected,
                eval_native,
                correlation_id=agent_response.correlation_id,
            )
            outcome_evaluation = comparison.to_dict()
            evidence_trace = trace.to_dict()

        if outcome_evaluation is None:
            outcome_evaluation = {
                "evaluation": "NOT_EVALUATED",
                "pattern": "NOT_EVALUATED",
                "semantic_authority": "NONE",
                "reason": "no native result available for comparison",
            }
            evidence_trace = {"correlation_id": agent_response.correlation_id, "semantic_authority": "NONE"}

        return GrokE2EResponse(
            agent_response=agent_response,
            outcome_evaluation=outcome_evaluation,
            evidence_trace=evidence_trace,
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
