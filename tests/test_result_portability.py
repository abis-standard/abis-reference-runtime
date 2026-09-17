"""Native Result and execution provenance portability — v0.5."""

from __future__ import annotations

import json
import tempfile
import unittest
from urllib.request import Request, urlopen

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.descriptor.constants import DESCRIPTOR_VERSION  # noqa: E402
from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.gateway.execution_surface import EXECUTION_SURFACE_REVISION  # noqa: E402
from abis_grp_runtime.gateway.reference_profile import PROFILE_VERSION  # noqa: E402
from abis_grp_runtime.gateway.server import start_external_gateway  # noqa: E402
from abis_grp_runtime.native_result import NativeResultEnvelope  # noqa: E402
from abis_grp_runtime.version import __version__  # noqa: E402
from tests._service import make_test_service  # noqa: E402

TEST_TOKEN = "test-gateway-token-reference-do-not-commit"

FORBIDDEN_TOP_LEVEL_ALIASES = (
    "reservation_id",
    "crs_native_result",
    "native_external_identifier",
)

AUTHORIZED_PROVENANCE_PATHS = (
    ("runtime", "name"),
    ("runtime", "version"),
    ("profile_version",),
    ("execution_surface_revision",),
    ("interaction", "vertical"),
    ("interaction", "operation"),
    ("descriptor_path",),
    ("descriptor_version",),
    ("business_system", "identifier"),
    ("business_system", "classification"),
)


def _get_path(data: dict, path: tuple[str, ...]) -> object:
    current: object = data
    for key in path:
        assert isinstance(current, dict)
        current = current[key]
    return current


def _restaurant_payload(correlation_id: str = "portability-restaurant-001") -> dict:
    return {
        "agent_id": "portability-agent",
        "agent_type": "reference-agent",
        "operation": "reserve",
        "execution_class": "CONTROLLED_SIMULATOR",
        "authorization_token": "ALLOW",
        "correlation_id": correlation_id,
        "input": {
            "date": "2026-09-12",
            "time": "20:00",
            "party_size": 2,
            "seating_type": "TABLE",
            "idempotency_key": correlation_id,
        },
    }


def _shopping_payload(correlation_id: str = "portability-shopping-001") -> dict:
    return {
        "agent_id": "portability-agent",
        "agent_type": "reference-agent",
        "operation": "submit_order",
        "execution_class": "CONTROLLED_SIMULATOR",
        "authorization_token": "ALLOW",
        "correlation_id": correlation_id,
        "input": {
            "sku_id": "SKU-DEMO-001",
            "quantity": 1,
            "idempotency_key": correlation_id,
        },
    }


class ResultPortabilityTestCase(unittest.TestCase):
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

    def _post(self, path: str, payload: dict) -> tuple[int, dict]:
        body = json.dumps(payload).encode()
        req = Request(
            f"{self.base}{path}",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {TEST_TOKEN}",
                "Content-Type": "application/json",
            },
        )
        with urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode())

    def _assert_neutral_invoke_body(self, body: dict, *, vertical: str, operation: str) -> None:
        for key in FORBIDDEN_TOP_LEVEL_ALIASES:
            self.assertNotIn(key, body, msg=f"forbidden top-level alias: {key}")
        native = body.get("native_result")
        self.assertIsInstance(native, dict)
        self.assertIn("technical_status", native)
        self.assertIn("external_status", native)
        provenance = body.get("execution_provenance")
        self.assertIsInstance(provenance, dict)
        for path in AUTHORIZED_PROVENANCE_PATHS:
            _get_path(provenance, path)
        self.assertEqual(provenance["runtime"]["version"], __version__)
        self.assertEqual(provenance["profile_version"], PROFILE_VERSION)
        self.assertEqual(provenance["execution_surface_revision"], EXECUTION_SURFACE_REVISION)
        self.assertEqual(provenance["interaction"]["vertical"], vertical)
        self.assertEqual(provenance["interaction"]["operation"], operation)
        self.assertEqual(provenance["descriptor_version"], DESCRIPTOR_VERSION)
        self.assertEqual(body["outcome_disposition"]["disposition"], "NOT_EVALUATED")
        self.assertFalse(
            NativeResultEnvelope(
                technical_status="TRANSPORT_OK",
                external_status=native.get("external_status"),
            ).implies_outcome_success()
        )

    def test_restaurant_invoke_response_neutrality(self) -> None:
        status, body = self._post("/v1/demo/restaurant/invoke", _restaurant_payload())
        self.assertEqual(status, 200)
        self._assert_neutral_invoke_body(body, vertical="restaurant", operation="reserve")
        self.assertEqual(body["native_result"]["external_status"], "CONFIRMED")
        self.assertIsNotNone(body["native_result"]["external_identifier"])
        self.assertEqual(
            provenance_business_system(body),
            "abis-demo-restaurant-simulator",
        )

    def test_shopping_invoke_response_neutrality(self) -> None:
        status, body = self._post("/v1/demo/shopping/invoke", _shopping_payload())
        self.assertEqual(status, 200)
        self._assert_neutral_invoke_body(body, vertical="shopping", operation="submit_order")
        self.assertEqual(body["native_result"]["external_status"], "ORDER_SUBMITTED")
        self.assertIsNotNone(body["native_result"]["external_identifier"])
        self.assertEqual(
            provenance_business_system(body),
            "abis-demo-commerce-simulator",
        )

    def test_result_consumed_without_aliases(self) -> None:
        status, body = self._post("/v1/demo/shopping/invoke", _shopping_payload("consume-001"))
        self.assertEqual(status, 200)
        native = body["native_result"]
        provenance = body["execution_provenance"]
        outcome = body["outcome_disposition"]
        observed_identifier = native["external_identifier"]
        observed_status = native["external_status"]
        runtime_version = provenance["runtime"]["version"]
        interaction = provenance["interaction"]
        self.assertTrue(observed_identifier)
        self.assertEqual(observed_status, "ORDER_SUBMITTED")
        self.assertEqual(runtime_version, __version__)
        self.assertEqual(interaction["vertical"], "shopping")
        self.assertEqual(outcome["disposition"], "NOT_EVALUATED")


def provenance_business_system(body: dict) -> str:
    provenance = body["execution_provenance"]
    business_system = provenance["business_system"]
    assert isinstance(business_system, dict)
    return str(business_system["identifier"])


if __name__ == "__main__":
    unittest.main()
