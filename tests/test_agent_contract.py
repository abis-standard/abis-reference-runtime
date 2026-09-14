"""External agent contract tests — stdlib unittest only."""

from __future__ import annotations

import json
import unittest

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.agent import (  # noqa: E402
    AgentRequestEnvelope,
    ExternalAgentAdapter,
    deserialize_request,
    serialize_request,
    serialize_response,
)
from abis_grp_runtime.agent.errors import AgentContractErrorCode  # noqa: E402


def _valid_request(**overrides: object) -> AgentRequestEnvelope:
    base = {
        "agent_id": "agent-generic-001",
        "agent_type": "reference-agent",
        "operation": "check_availability",
        "execution_class": "NULL",
        "authorization_token": "ALLOW",
        "correlation_id": "corr-test-001",
        "request_id": "req-test-001",
        "structured_input": {"slot": "2026-09-10T19:00:00Z"},
    }
    base.update(overrides)
    return AgentRequestEnvelope(**base)


class TestAgentRequestEntry(unittest.TestCase):
    def test_valid_request_enters_runtime(self) -> None:
        adapter = ExternalAgentAdapter()
        response = adapter.invoke(_valid_request())
        self.assertEqual(response.transport_status, "ACCEPTED")
        self.assertIsNotNone(response.native_result)

    def test_correlation_propagates(self) -> None:
        adapter = ExternalAgentAdapter()
        response = adapter.invoke(_valid_request(correlation_id="corr-fixed-42"))
        self.assertEqual(response.correlation_id, "corr-fixed-42")


class TestExecutionPolicy(unittest.TestCase):
    def test_real_external_denied(self) -> None:
        adapter = ExternalAgentAdapter()
        response = adapter.invoke(_valid_request(execution_class="REAL_EXTERNAL"))
        self.assertEqual(response.transport_status, "REJECTED")
        self.assertEqual(response.error.code, AgentContractErrorCode.EXECUTION_CLASS_DENIED)


class TestResponseSeparation(unittest.TestCase):
    def test_native_result_separate_from_outcome(self) -> None:
        adapter = ExternalAgentAdapter()
        response = adapter.invoke(_valid_request(execution_class="FIXTURE", operation="reserve"))
        self.assertEqual(response.outcome_disposition["disposition"], "NOT_EVALUATED")


class TestSerializationRoundTrip(unittest.TestCase):
    def test_json_round_trip(self) -> None:
        request = _valid_request()
        payload = serialize_request(request)
        restored = deserialize_request(payload)
        adapter = ExternalAgentAdapter()
        response = adapter.invoke(restored)
        serialized = serialize_response(response)
        parsed = json.loads(serialized)
        self.assertEqual(parsed["correlation_id"], "corr-test-001")


if __name__ == "__main__":
    unittest.main()
