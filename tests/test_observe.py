"""Async technical observation — v0.6 narrow scope."""

from __future__ import annotations

import json
import tempfile
import unittest
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.gateway.server import start_external_gateway  # noqa: E402
from tests._service import make_test_service  # noqa: E402

TEST_TOKEN = "test-observe-token-reference-do-not-commit"


def _pending_invoke_payload(correlation_id: str) -> dict:
    return {
        "agent_id": "reference-agent-observe-001",
        "agent_type": "reference-agent",
        "operation": "reserve",
        "execution_class": "CONTROLLED_SIMULATOR",
        "authorization_token": "ALLOW",
        "correlation_id": correlation_id,
        "input": {
            "date": "2026-09-12",
            "time": "20:00",
            "party_size": 2,
            "seating_type": "PRIVATE_ROOM",
            "customer_reference": "TEST-CUST-OBSERVE",
            "idempotency_key": f"idem-{correlation_id}",
            "test_scenario": "PENDING",
        },
    }


class ObserveGatewayTestCase(unittest.TestCase):
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

    def _post(self, path: str, payload: dict, *, token: str = TEST_TOKEN) -> tuple[int, dict]:
        headers = {"Content-Type": "application/json"}
        if token:
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
            return exc.code, json.loads(exc.read().decode())


class TestObserveFlow(ObserveGatewayTestCase):
    def test_pending_invoke_then_observe(self) -> None:
        correlation = "observe-flow-001"
        icr = str(uuid.uuid4())
        invoke_status, invoke_body = self._post(
            "/v1/demo/restaurant/invoke",
            {**_pending_invoke_payload(correlation), "implementation_continuity_reference": icr},
        )
        self.assertEqual(invoke_status, 200)
        self.assertEqual(invoke_body["native_result"]["external_status"], "PENDING")
        external_id = invoke_body["native_result"]["external_identifier"]
        self.assertTrue(external_id)

        observe_status, observe_body = self._post(
            "/v1/demo/restaurant/observe",
            {
                "correlation_id": "observe-correlation-001",
                "external_identifier": external_id,
                "implementation_continuity_reference": icr,
            },
        )
        self.assertEqual(observe_status, 200)
        self.assertEqual(observe_body["native_result"]["external_identifier"], external_id)
        self.assertEqual(observe_body["native_result"]["external_status"], "PENDING")
        self.assertEqual(observe_body["implementation_continuity_reference"], icr)
        self.assertEqual(observe_body["outcome_disposition"]["disposition"], "NOT_EVALUATED")
        provenance = observe_body.get("execution_provenance") or {}
        self.assertEqual(provenance.get("interaction", {}).get("operation"), "observe")
        self.assertEqual(provenance.get("observation_kind"), "native_technical_observation")

    def test_observe_without_icr_valid(self) -> None:
        correlation = "observe-no-icr-001"
        _, invoke_body = self._post(
            "/v1/demo/restaurant/invoke",
            _pending_invoke_payload(correlation),
        )
        external_id = invoke_body["native_result"]["external_identifier"]
        status, body = self._post(
            "/v1/demo/restaurant/observe",
            {
                "correlation_id": "observe-correlation-002",
                "external_identifier": external_id,
            },
        )
        self.assertEqual(status, 200)
        self.assertIsNone(body.get("implementation_continuity_reference"))

    def test_unknown_external_identifier_deterministic(self) -> None:
        status, body = self._post(
            "/v1/demo/restaurant/observe",
            {
                "correlation_id": "observe-missing-001",
                "external_identifier": "TEST-RSV-MISSING-999",
            },
        )
        self.assertEqual(status, 422)
        native = body.get("native_result") or {}
        crs = (native.get("payload") or {}).get("crs_native_result") or {}
        self.assertEqual(crs.get("error"), "NOT_FOUND")
        self.assertEqual(body["outcome_disposition"]["disposition"], "NOT_EVALUATED")

    def test_observe_requires_auth(self) -> None:
        req = Request(
            f"{self.base}/v1/demo/restaurant/observe",
            data=json.dumps(
                {"correlation_id": "x", "external_identifier": "TEST-RSV-1"}
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req, timeout=5)
        self.assertEqual(ctx.exception.code, 401)

    def test_shopping_observe_not_supported(self) -> None:
        status, body = self._post(
            "/v1/demo/shopping/observe",
            {"correlation_id": "x", "external_identifier": "ORD-1"},
        )
        self.assertEqual(status, 403)
        self.assertEqual(body["error"]["code"], "REQUEST_INVALID")
