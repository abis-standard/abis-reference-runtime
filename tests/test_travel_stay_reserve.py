"""Travel stay_reserve vertical — CONTROLLED_SIMULATOR only."""

from __future__ import annotations

import json
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.adapters.errors import AdapterValidationError  # noqa: E402
from abis_grp_runtime.adapters.travel import TravelStayReserveAdapter  # noqa: E402
from abis_grp_runtime.connectors.travel_stay_simulator import (  # noqa: E402
    TravelStaySimulatorConnector,
    travel_dict_to_native_envelope,
)
from abis_grp_runtime.e2e.service import GrokE2EService  # noqa: E402
from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.gateway.preflight import PREFLIGHT_EXECUTION_DENIED, PREFLIGHT_READY  # noqa: E402
from abis_grp_runtime.gateway.server import start_external_gateway  # noqa: E402
from abis_grp_runtime.registry.factory import build_reference_registry  # noqa: E402
from crs.engine import ReservationEngine  # noqa: E402
from css.engine import CommerceEngine  # noqa: E402
from tests._service import make_test_service  # noqa: E402

TEST_TOKEN = "test-gateway-token-reference-do-not-commit"
OPAQUE_OFFER = "OPAQUE-OFFER-FIXTURE-001-NOT-A-REAL-RATE"


def _valid_input(**overrides: object) -> dict:
    payload = {
        "stay": {"check_in": "2026-11-01", "check_out": "2026-11-02"},
        "occupancy": {"rooms": 1, "adults": 2, "children": 0},
        "holder": {"name": "ABIS", "surname": "Test"},
        "guests": [
            {"room_id": 1, "type": "AD", "name": "Test", "surname": "AdultOne"},
            {"room_id": 1, "type": "AD", "name": "Test", "surname": "AdultTwo"},
        ],
        "selected_offer_reference": OPAQUE_OFFER,
        "client_reference": "ABIS-TRAVEL-C1",
        "idempotency_key": "idem-travel-c1",
    }
    payload.update(overrides)
    return payload


def _invoke_payload(**overrides: object) -> dict:
    payload = {
        "agent_id": "reference-agent-001",
        "agent_type": "reference-agent",
        "operation": "stay_reserve",
        "execution_class": "CONTROLLED_SIMULATOR",
        "authorization_token": "ALLOW",
        "correlation_id": "travel-invoke-001",
        "input": _valid_input(),
    }
    payload.update(overrides)
    return payload


class TravelAdapterValidationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = TravelStayReserveAdapter()

    def test_invalid_stay_dates(self) -> None:
        with self.assertRaises(AdapterValidationError):
            self.adapter.validate_structured_input(
                "stay_reserve",
                _valid_input(stay={"check_in": "2026-11-02", "check_out": "2026-11-01"}),
            )

    def test_invalid_occupancy(self) -> None:
        with self.assertRaises(AdapterValidationError):
            self.adapter.validate_structured_input(
                "stay_reserve",
                _valid_input(occupancy={"rooms": 0, "adults": 1, "children": 0}),
            )

    def test_empty_offer_reference(self) -> None:
        with self.assertRaises(AdapterValidationError):
            self.adapter.validate_structured_input(
                "stay_reserve",
                _valid_input(selected_offer_reference=""),
            )

    def test_descriptor_developer_preview(self) -> None:
        descriptor = self.adapter.get_descriptor("stay_reserve")
        self.assertEqual(descriptor["vertical"], "travel")
        self.assertEqual(descriptor["operation"], "stay_reserve")
        self.assertEqual(descriptor["implementation_maturity"], "DEVELOPER_PREVIEW")
        self.assertEqual(descriptor["execution_classes_allowed"], ["CONTROLLED_SIMULATOR"])


class TravelSimulatorTestCase(unittest.TestCase):
    def test_opaque_reference_not_in_native_payload(self) -> None:
        connector = TravelStaySimulatorConnector()
        native = connector.execute("stay_reserve", _valid_input())
        blob = json.dumps(native.payload)
        self.assertNotIn(OPAQUE_OFFER, blob)
        self.assertTrue(native.payload["simulator_native_result"]["offer_reference_supplied"])

    def test_native_envelope_does_not_imply_outcome(self) -> None:
        native = travel_dict_to_native_envelope(
            {"transport_ok": True, "status": "SIMULATED_TECHNICAL_SUCCESS", "stay_reference": "SYN-STAY-1"},
            operation="stay_reserve",
        )
        self.assertFalse(native.implies_outcome_success())


class TravelGatewayTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.evidence_path = f"{self.tmp.name}/evidence.jsonl"
        self.service = make_test_service(self.tmp.name)
        self.config = GatewayConfig(
            host="127.0.0.1",
            port=0,
            bearer_token=TEST_TOKEN,
            max_body_bytes=65536,
            requests_per_minute=120,
            max_concurrent=8,
            evidence_log_path=self.evidence_path,
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

    def test_preflight_ready(self) -> None:
        status, body = self._post(
            "/v1/demo/travel/preflight",
            {"operation": "stay_reserve", "execution_class": "CONTROLLED_SIMULATOR"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["preflight_state"], PREFLIGHT_READY)

    def test_preflight_denies_authorized_non_production(self) -> None:
        status, body = self._post(
            "/v1/demo/travel/preflight",
            {"operation": "stay_reserve", "execution_class": "AUTHORIZED_NON_PRODUCTION"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["preflight_state"], PREFLIGHT_EXECUTION_DENIED)

    def test_invoke_success_not_evaluated(self) -> None:
        status, body = self._post("/v1/demo/travel/invoke", _invoke_payload())
        self.assertEqual(status, 200)
        self.assertEqual(body["transport_status"], "ACCEPTED")
        native = body["native_result"]
        self.assertEqual(native["technical_status"], "TRANSPORT_OK")
        self.assertEqual(body["outcome_disposition"]["disposition"], "NOT_EVALUATED")
        self.assertNotIn(OPAQUE_OFFER, json.dumps(body))

    def test_evidence_log_excludes_opaque_offer(self) -> None:
        self._post("/v1/demo/travel/invoke", _invoke_payload(correlation_id="travel-evidence-001"))
        with open(self.evidence_path, encoding="utf-8") as handle:
            log_text = handle.read()
        self.assertNotIn(OPAQUE_OFFER, log_text)

    def test_observe_unsupported(self) -> None:
        status, body = self._post(
            "/v1/demo/travel/observe",
            {"correlation_id": "travel-obs-001", "external_identifier": "SYN-STAY-1"},
        )
        self.assertEqual(status, 403)

    def test_authorized_non_production_unavailable(self) -> None:
        registry = build_reference_registry(
            ReservationEngine(data_dir=self.tmp.name),
            CommerceEngine(),
        )
        service = GrokE2EService(registry)
        adapter = registry.get_adapter("travel", "stay_reserve")
        with self.assertRaises(ValueError):
            adapter.get_connector_for_execution_class("AUTHORIZED_NON_PRODUCTION")


if __name__ == "__main__":
    unittest.main()
