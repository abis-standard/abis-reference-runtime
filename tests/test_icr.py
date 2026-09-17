"""Implementation Continuity Reference — v0.6 narrow scope."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.agent.continuity_reference import (  # noqa: E402
    ICR_MAX_LENGTH,
    generate_icr,
    validate_icr,
)
from abis_grp_runtime.agent.envelope import AgentRequestEnvelope  # noqa: E402
from abis_grp_runtime.agent.adapter import ExternalAgentAdapter  # noqa: E402
from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.gateway.server import start_external_gateway  # noqa: E402
from tests._service import make_test_service  # noqa: E402

TEST_TOKEN = "test-icr-token-reference-do-not-commit"


def _reserve_payload(**overrides) -> dict:
    payload = {
        "agent_id": "reference-agent-icr-001",
        "agent_type": "reference-agent",
        "operation": "reserve",
        "execution_class": "CONTROLLED_SIMULATOR",
        "authorization_token": "ALLOW",
        "correlation_id": "icr-correlation-001",
        "input": {
            "date": "2026-09-12",
            "time": "20:00",
            "party_size": 2,
            "seating_type": "PRIVATE_ROOM",
            "customer_reference": "TEST-CUST-ICR",
            "idempotency_key": "idem-icr-001",
            "test_scenario": "NORMAL_SUCCESS",
        },
    }
    payload.update(overrides)
    return payload


class TestIcrValidation(unittest.TestCase):
    def test_generate_is_uuid(self) -> None:
        value = generate_icr()
        uuid.UUID(value)

    def test_max_length_enforced(self) -> None:
        error = validate_icr("x" * (ICR_MAX_LENGTH + 1))
        self.assertIsNotNone(error)

    def test_secret_like_rejected(self) -> None:
        self.assertIsNotNone(validate_icr("Bearer abcdef123456"))

    def test_forbidden_equals_rejected(self) -> None:
        self.assertIsNotNone(validate_icr("same-key", forbidden_equals=("same-key",)))


class TestIcrGateway(unittest.TestCase):
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
        req = Request(
            f"{self.base}{path}",
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

    def test_omitted_icr_generates_opaque_value(self) -> None:
        status, body = self._post("/v1/demo/restaurant/invoke", _reserve_payload())
        self.assertEqual(status, 200)
        icr = body.get("implementation_continuity_reference")
        self.assertIsNotNone(icr)
        uuid.UUID(str(icr))

    def test_client_icr_accepted_and_propagated(self) -> None:
        client_icr = str(uuid.uuid4())
        status, body = self._post(
            "/v1/demo/restaurant/invoke",
            _reserve_payload(implementation_continuity_reference=client_icr),
        )
        self.assertEqual(status, 200)
        self.assertEqual(body.get("implementation_continuity_reference"), client_icr)
        provenance = body.get("execution_provenance") or {}
        self.assertEqual(provenance.get("implementation_continuity_reference"), client_icr)

    def test_icr_must_not_equal_idempotency_key(self) -> None:
        status, body = self._post(
            "/v1/demo/restaurant/invoke",
            _reserve_payload(implementation_continuity_reference="idem-icr-001"),
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "REQUEST_INVALID")

    def test_icr_does_not_replace_external_identifier(self) -> None:
        status, body = self._post("/v1/demo/restaurant/invoke", _reserve_payload())
        self.assertEqual(status, 200)
        icr = body["implementation_continuity_reference"]
        external_id = body["native_result"]["external_identifier"]
        self.assertNotEqual(icr, external_id)

    def test_same_icr_accompanies_retry(self) -> None:
        client_icr = str(uuid.uuid4())
        payload = _reserve_payload(
            implementation_continuity_reference=client_icr,
            correlation_id="icr-retry-001",
        )
        status1, body1 = self._post("/v1/demo/restaurant/invoke", payload)
        status2, body2 = self._post("/v1/demo/restaurant/invoke", payload)
        self.assertEqual(status1, 200)
        self.assertEqual(status2, 200)
        self.assertEqual(body1["implementation_continuity_reference"], client_icr)
        self.assertEqual(body2["implementation_continuity_reference"], client_icr)
        self.assertEqual(
            body1["native_result"]["external_identifier"],
            body2["native_result"]["external_identifier"],
        )

    def test_different_icr_does_not_change_idempotency(self) -> None:
        base = _reserve_payload(correlation_id="icr-idem-002")
        status1, body1 = self._post(
            "/v1/demo/restaurant/invoke",
            {**base, "implementation_continuity_reference": str(uuid.uuid4())},
        )
        status2, body2 = self._post(
            "/v1/demo/restaurant/invoke",
            {**base, "implementation_continuity_reference": str(uuid.uuid4())},
        )
        self.assertEqual(status1, 200)
        self.assertEqual(status2, 200)
        self.assertEqual(
            body1["native_result"]["external_identifier"],
            body2["native_result"]["external_identifier"],
        )


class TestIcrSemanticIsolation(unittest.TestCase):
    def test_icr_does_not_alter_implementation_interaction_derivation(self) -> None:
        adapter = ExternalAgentAdapter()
        correlation = "semantic-iso-001"
        client_icr = str(uuid.uuid4())
        request = AgentRequestEnvelope(
            agent_id="agent-001",
            operation="reserve",
            execution_class="FIXTURE",
            authorization_token="ALLOW",
            correlation_id=correlation,
            implementation_continuity_reference=client_icr,
        )
        response = adapter.invoke(request)
        impl_interaction = f"impl-interaction-{correlation}"
        trace_events = (response.trace_reference or {}).get("events", [])
        semantic_events = [e for e in trace_events if e.get("phase") == "semantic_boundary"]
        self.assertTrue(semantic_events)
        self.assertEqual(semantic_events[0]["detail"]["interaction_id"], impl_interaction)
        self.assertNotEqual(response.implementation_continuity_reference, impl_interaction)
