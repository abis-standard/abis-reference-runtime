"""Machine-readable request construction from Profile + Descriptor only."""

from __future__ import annotations

import json
import tempfile
import unittest
from urllib.request import urlopen

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.gateway.server import start_external_gateway  # noqa: E402
from tests._service import make_test_service  # noqa: E402

TEST_TOKEN = "test-gateway-token-reference-do-not-commit"


def build_invoke_payload_from_contract(
    profile: dict,
    descriptor: dict,
    *,
    vertical: str,
    operation: str,
    execution_class: str,
    structured_values: dict,
) -> dict:
    """Generic agent — no adapter imports."""
    interaction = next(
        i
        for i in profile["advertised_interactions"]
        if i["vertical"] == vertical and i["operation"] == operation
    )
    assert interaction["descriptor_path"] == descriptor["descriptor_path"]
    assert execution_class in interaction["execution_classes_allowed"]
    spec = descriptor["structured_input"]
    required = set(spec.get("required_fields") or [])
    for field in required:
        if field not in structured_values:
            raise ValueError(f"missing required field: {field}")
    envelope = descriptor["request_envelope"]
    payload = {
        "agent_id": "machine-readability-agent",
        "agent_type": "reference-agent",
        "operation": operation,
        "execution_class": execution_class,
        "authorization_token": "ALLOW",
        "correlation_id": "machine-readability-001",
        envelope["input_field"]: structured_values,
    }
    return payload


class MachineReadabilityTestCase(unittest.TestCase):
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

    def _get(self, path: str) -> dict:
        with urlopen(f"{self.base}{path}", timeout=5) as resp:
            return json.loads(resp.read().decode())

    def test_restaurant_request_from_profile_and_descriptor(self) -> None:
        profile = self._get("/v1/reference-profile")
        descriptor = self._get("/v1/reference-profile/interactions/restaurant/reserve")
        payload = build_invoke_payload_from_contract(
            profile,
            descriptor,
            vertical="restaurant",
            operation="reserve",
            execution_class="CONTROLLED_SIMULATOR",
            structured_values={
                "date": "2026-09-12",
                "time": "20:00",
                "party_size": 2,
                "seating_type": "TABLE",
                "idempotency_key": "machine-restaurant-001",
            },
        )
        self.assertEqual(descriptor["preflight"]["path"], "/v1/demo/restaurant/preflight")
        self.assertEqual(descriptor["invocation"]["path"], "/v1/demo/restaurant/invoke")
        self.assertTrue(descriptor["authorization"]["invoke"]["required"])

    def test_shopping_request_from_profile_and_descriptor(self) -> None:
        profile = self._get("/v1/reference-profile")
        descriptor = self._get("/v1/reference-profile/interactions/shopping/submit_order")
        payload = build_invoke_payload_from_contract(
            profile,
            descriptor,
            vertical="shopping",
            operation="submit_order",
            execution_class="CONTROLLED_SIMULATOR",
            structured_values={
                "sku_id": "SKU-DEMO-001",
                "quantity": 1,
                "idempotency_key": "machine-shopping-001",
            },
        )
        self.assertIn("sku_id", payload["input"])
        self.assertEqual(descriptor["structured_input"]["field_types"]["quantity"], "integer")


if __name__ == "__main__":
    unittest.main()
