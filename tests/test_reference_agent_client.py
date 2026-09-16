"""Reference Agent Client tests — PROFILE → PREFLIGHT → INVOKE."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.agent.reference_client import (  # noqa: E402
    ReferenceAgentClient,
    ReferenceClientConfig,
    ReferenceClientError,
)
from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.gateway.preflight import (  # noqa: E402
    PREFLIGHT_EXECUTION_DENIED,
    PREFLIGHT_NOT_ADVERTISED,
    PREFLIGHT_READY,
)
from abis_grp_runtime.gateway.reference_profile import PROFILE_KIND  # noqa: E402
from abis_grp_runtime.gateway.server import start_external_gateway  # noqa: E402
from tests._profile_helpers import valid_descriptor, valid_profile  # noqa: E402
from tests._service import make_test_service  # noqa: E402

TEST_TOKEN = "test-gateway-token-reference-do-not-commit"


def _invoke_payload(*, correlation_id: str = "ref-client-e2e-001") -> dict:
    return {
        "agent_id": "reference-agent-001",
        "agent_type": "reference-agent",
        "operation": "reserve",
        "execution_class": "CONTROLLED_SIMULATOR",
        "authorization_token": "ALLOW",
        "correlation_id": correlation_id,
        "input": {
            "date": "2026-09-12",
            "time": "20:00",
            "party_size": 4,
            "seating_type": "PRIVATE_ROOM",
            "customer_reference": "TEST-CUST-REF-CLIENT",
            "idempotency_key": f"idem-{correlation_id}",
            "test_scenario": "NORMAL_SUCCESS",
        },
    }


class GatewayServerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.service = make_test_service(self.tmp.name)
        self.config = GatewayConfig(
            host="127.0.0.1",
            port=0,
            bearer_token=TEST_TOKEN,
            max_body_bytes=65536,
            requests_per_minute=120,
            max_concurrent=8,
        )
        self.httpd, self.port, _ = start_external_gateway(self.service, self.config)
        self.base_url = f"http://127.0.0.1:{self.port}"

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.tmp.cleanup()

    def _client(self, **overrides: object) -> ReferenceAgentClient:
        config = ReferenceClientConfig(
            base_url=self.base_url,
            vertical=str(overrides.pop("vertical", "restaurant")),
            operation=str(overrides.pop("operation", "reserve")),
            execution_class=str(overrides.pop("execution_class", "CONTROLLED_SIMULATOR")),
            gateway_token=overrides.pop("gateway_token", TEST_TOKEN),
        )
        return ReferenceAgentClient(config)

    def _reservation_count(self) -> int:
        state_path = Path(self.tmp.name) / "state.json"
        if not state_path.is_file():
            return 0
        state = json.loads(state_path.read_text(encoding="utf-8"))
        return len(state.get("reservations") or {})


class TestReferenceClientUnit(unittest.TestCase):
    def test_validate_profile_rejects_malformed(self) -> None:
        with self.assertRaises(ReferenceClientError):
            ReferenceAgentClient.validate_profile({"profile_kind": "wrong"})

    def test_validate_invoke_target_rejects_absolute_url(self) -> None:
        with self.assertRaises(ReferenceClientError):
            ReferenceAgentClient.validate_invoke_target(
                {"method": "POST", "path": "https://evil.example/invoke"}
            )

    def test_locate_interaction_missing(self) -> None:
        with self.assertRaises(ReferenceClientError):
            ReferenceAgentClient.locate_interaction(
                valid_profile(),
                vertical="restaurant",
                operation="modify",
            )


class TestReferenceClientPositiveE2E(GatewayServerTestCase):
    def test_profile_preflight_invoke_flow(self) -> None:
        client = self._client()
        result = client.execute(_invoke_payload())
        self.assertTrue(result.profile_checked)
        self.assertTrue(result.descriptor_checked)
        self.assertEqual(result.preflight_state, PREFLIGHT_READY)
        self.assertTrue(result.invoke_attempted)
        self.assertEqual(result.transport_status, "ACCEPTED")
        self.assertEqual(result.native_external_status, "CONFIRMED")
        self.assertEqual(result.outcome_disposition, "NOT_EVALUATED")
        self.assertIsNotNone(result.trace_reference)
        self.assertNotIn("outcome_evaluation", json.dumps(result.invoke_response or {}))
        self.assertEqual(self._reservation_count(), 1)

    def test_dynamic_invoke_path_from_profile(self) -> None:
        client = self._client()
        captured: dict[str, str] = {}
        original_invoke = ReferenceAgentClient.invoke

        def _capture_invoke(self_client: ReferenceAgentClient, path: str, payload: dict) -> dict:
            captured["path"] = path
            return original_invoke(self_client, path, payload)

        with patch.object(client, "fetch_profile", return_value=valid_profile()):
            with patch.object(client, "fetch_descriptor", return_value=valid_descriptor()):
                with patch.object(
                    client,
                    "run_preflight",
                    return_value={
                        "preflight_state": PREFLIGHT_READY,
                        "invocation": {"method": "POST", "path": "/v1/demo/restaurant/invoke"},
                    },
                ):
                    with patch.object(client, "invoke", side_effect=lambda path, payload: _capture_invoke(client, path, payload)):
                        result = client.execute(_invoke_payload(correlation_id="dynamic-path-001"))
        self.assertTrue(result.invoke_attempted)
        self.assertEqual(captured["path"], "/v1/demo/restaurant/invoke")

    def test_idempotency_preserved(self) -> None:
        client = self._client()
        payload = _invoke_payload(correlation_id="ref-client-idem-001")
        first = client.execute(payload)
        second = client.execute(payload)
        self.assertTrue(first.invoke_attempted)
        self.assertTrue(second.invoke_attempted)
        self.assertEqual(first.reservation_id, second.reservation_id)
        self.assertEqual(self._reservation_count(), 1)


class TestReferenceClientNegativeE2E(GatewayServerTestCase):
    def test_modify_not_advertised_fail_closed(self) -> None:
        client = self._client(operation="modify")
        result = client.execute(_invoke_payload(correlation_id="neg-modify-001"))
        self.assertFalse(result.invoke_attempted)
        self.assertEqual(self._reservation_count(), 0)

    def test_real_external_execution_denied(self) -> None:
        client = self._client(execution_class="REAL_EXTERNAL")
        result = client.execute(_invoke_payload(correlation_id="neg-real-ext-001"))
        self.assertFalse(result.invoke_attempted)
        self.assertEqual(result.preflight_state, PREFLIGHT_EXECUTION_DENIED)
        self.assertEqual(self._reservation_count(), 0)

    def test_malformed_profile_fail_closed(self) -> None:
        client = self._client()
        with patch.object(client, "fetch_profile", return_value={"profile_kind": "broken"}):
            result = client.execute(_invoke_payload(correlation_id="neg-profile-001"))
        self.assertFalse(result.invoke_attempted)
        self.assertFalse(result.profile_checked)

    def test_absolute_invoke_url_rejected(self) -> None:
        client = self._client()
        with patch.object(
            client,
            "fetch_profile",
            return_value=valid_profile(invoke_path="https://evil.example/invoke"),
        ):
            with patch.object(client, "fetch_descriptor", return_value=valid_descriptor(invoke_path="https://evil.example/invoke")):
                result = client.execute(_invoke_payload(correlation_id="neg-abs-url-001"))
        self.assertFalse(result.invoke_attempted)

    def test_missing_token_prevents_invoke(self) -> None:
        client = self._client(gateway_token=None)
        result = client.execute(_invoke_payload(correlation_id="neg-no-token-001"))
        self.assertTrue(result.profile_checked)
        self.assertEqual(result.preflight_state, PREFLIGHT_READY)
        self.assertFalse(result.invoke_attempted)
        self.assertEqual(self._reservation_count(), 0)

    def test_not_advertised_vertical(self) -> None:
        client = self._client(vertical="travel")
        result = client.execute(_invoke_payload(correlation_id="neg-travel-001"))
        self.assertFalse(result.invoke_attempted)
        self.assertIn(result.error or "", ("requested interaction not present in profile", "preflight not ready"))


if __name__ == "__main__":
    unittest.main()
