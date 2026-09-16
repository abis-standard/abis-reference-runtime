"""Reference runtime gateway tests — NORMAL_SUCCESS focus."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.gateway.server import start_external_gateway  # noqa: E402
from tests._service import make_test_service  # noqa: E402

TEST_TOKEN = "test-gateway-token-reference-do-not-commit"


def _normal_success_payload() -> dict:
    return {
        "agent_id": "reference-agent-001",
        "agent_type": "reference-agent",
        "operation": "reserve",
        "execution_class": "CONTROLLED_SIMULATOR",
        "authorization_token": "ALLOW",
        "correlation_id": "gw-normal-success-001",
        "input": {
            "date": "2026-09-12",
            "time": "20:00",
            "party_size": 4,
            "seating_type": "PRIVATE_ROOM",
            "customer_reference": "TEST-CUST-GW-REFERENCE",
            "idempotency_key": "idem-gw-normal-success-001",
            "test_scenario": "NORMAL_SUCCESS",
        },
    }


class GatewayTestCase(unittest.TestCase):
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
        self.base = f"http://127.0.0.1:{self.port}"

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.tmp.cleanup()

    def _post(self, path: str, payload: dict, *, token: str | None = TEST_TOKEN) -> tuple[int, dict]:
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        req = Request(
            f"{self.base}{path}",
            data=json.dumps(payload).encode(),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode())
        except HTTPError as exc:
            body = json.loads(exc.read().decode())
            return exc.code, body


class TestGatewaySecurity(GatewayTestCase):
    def test_missing_bearer_denied(self) -> None:
        status, body = self._post("/v1/demo/restaurant/invoke", _normal_success_payload(), token=None)
        self.assertEqual(status, 401)
        self.assertEqual(body["error"]["code"], "AUTHENTICATION_DENIED")

    def test_real_external_denied(self) -> None:
        payload = _normal_success_payload()
        payload["execution_class"] = "REAL_EXTERNAL"
        status, body = self._post("/v1/demo/restaurant/invoke", payload)
        self.assertEqual(status, 403)
        self.assertEqual(body["error"]["code"], "EXECUTION_CLASS_DENIED")


class TestGatewayNormalSuccess(GatewayTestCase):
    def test_normal_success_native_result(self) -> None:
        status, body = self._post("/v1/demo/restaurant/invoke", _normal_success_payload())
        self.assertEqual(status, 200)
        self.assertEqual(body["transport_status"], "ACCEPTED")
        self.assertEqual(body["correlation_id"], "gw-normal-success-001")
        self.assertEqual(body["native_result"]["external_status"], "CONFIRMED")
        self.assertEqual(body["outcome_disposition"]["disposition"], "NOT_EVALUATED")
        self.assertIsNotNone(body["native_result"]["external_identifier"])
        self.assertNotIn("reservation_id", body)
        self.assertNotIn("crs_native_result", body)
        self.assertNotIn("native_external_identifier", body)
        self.assertIn("execution_provenance", body)
        self.assertNotIn("outcome_evaluation", body)
        self.assertNotIn("evidence_trace", body)

    def test_trace_reference_present(self) -> None:
        status, body = self._post("/v1/demo/restaurant/invoke", _normal_success_payload())
        self.assertEqual(status, 200)
        trace = body.get("trace_reference") or {}
        self.assertEqual(trace.get("correlation_id"), "gw-normal-success-001")
        phases = [event.get("phase") for event in trace.get("events", [])]
        self.assertIn("authorization", phases)
        self.assertIn("native_result", phases)
        self.assertIn("outcome_interpreter", phases)

    def test_state_json_mutated(self) -> None:
        self._post("/v1/demo/restaurant/invoke", _normal_success_payload())
        state_path = Path(self.tmp.name) / "state.json"
        self.assertTrue(state_path.is_file())
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertTrue(state.get("reservations"))

    def test_idempotency_replay(self) -> None:
        status1, body1 = self._post("/v1/demo/restaurant/invoke", _normal_success_payload())
        status2, body2 = self._post("/v1/demo/restaurant/invoke", _normal_success_payload())
        self.assertEqual(status1, 200)
        self.assertEqual(status2, 200)
        self.assertEqual(
            body1["native_result"]["external_identifier"],
            body2["native_result"]["external_identifier"],
        )
        state = json.loads((Path(self.tmp.name) / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(len(state["reservations"]), 1)


class TestGatewayGenericValidation(unittest.TestCase):
    VERTICAL_SPECIFIC_FIELDS = (
        "party_size",
        "seating_type",
        "sku_id",
        '"date"',
        '"time"',
        '"quantity"',
    )

    def test_validation_module_has_no_vertical_field_coupling(self) -> None:
        from pathlib import Path

        source = (
            Path(__file__).resolve().parents[1]
            / "runtime"
            / "src"
            / "abis_grp_runtime"
            / "gateway"
            / "validation.py"
        ).read_text(encoding="utf-8")
        for token in self.VERTICAL_SPECIFIC_FIELDS:
            self.assertNotIn(token, source, msg=f"vertical-specific token present: {token}")


class TestGatewayStartup(unittest.TestCase):
    def test_missing_token_blocks_startup(self) -> None:
        config = GatewayConfig(host="127.0.0.1", port=0, bearer_token=None)
        with self.assertRaises(ValueError):
            config.validate_startup()


if __name__ == "__main__":
    unittest.main()
