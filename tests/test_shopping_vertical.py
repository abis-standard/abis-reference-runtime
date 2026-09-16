"""Shopping vertical invoke and validation tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.gateway.server import start_external_gateway  # noqa: E402
from tests._service import make_test_service  # noqa: E402

TEST_TOKEN = "test-gateway-token-reference-do-not-commit"


def _shopping_payload(**overrides: object) -> dict:
    payload = {
        "agent_id": "reference-agent-001",
        "agent_type": "reference-agent",
        "operation": "submit_order",
        "execution_class": "CONTROLLED_SIMULATOR",
        "authorization_token": "ALLOW",
        "correlation_id": "shopping-invoke-001",
        "input": {
            "sku_id": "SKU-DEMO-001",
            "quantity": 1,
            "idempotency_key": "idem-shopping-001",
            "test_scenario": "NORMAL_SUCCESS",
        },
    }
    payload.update(overrides)
    return payload


class ShoppingVerticalTestCase(unittest.TestCase):
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

    def _invoke(self, payload: dict) -> tuple[int, dict]:
        req = Request(
            f"{self.base}/v1/demo/shopping/invoke",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {TEST_TOKEN}",
            },
            method="POST",
        )
        try:
            with urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode())
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode())

    def test_submit_order_success(self) -> None:
        status, body = self._invoke(_shopping_payload())
        self.assertEqual(status, 200)
        self.assertEqual(body["transport_status"], "ACCEPTED")
        native = body["native_result"]
        self.assertEqual(native["external_status"], "ORDER_SUBMITTED")
        self.assertIsNotNone(native.get("external_identifier"))
        self.assertEqual(body["outcome_disposition"]["disposition"], "NOT_EVALUATED")

    def test_rejects_payment_field(self) -> None:
        payload = _shopping_payload()
        payload["input"]["payment_token"] = "tok_test"
        status, body = self._invoke(payload)
        self.assertEqual(status, 400)
        self.assertIn("error", body)

    def test_rejects_pii_email(self) -> None:
        payload = _shopping_payload()
        payload["input"]["email"] = "user@example.com"
        status, body = self._invoke(payload)
        self.assertEqual(status, 400)
        self.assertIn("error", body)


if __name__ == "__main__":
    unittest.main()
