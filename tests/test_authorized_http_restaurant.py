"""Authorized non-production HTTP adapter — restaurant reserve."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
from http.server import HTTPServer
from typing import Any
from pathlib import Path
import sys

from tests._bootstrap import ensure_paths

ensure_paths()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from abis_grp_runtime.adapters.http_adapter_config import RestaurantHttpAdapterConfig  # noqa: E402
from abis_grp_runtime.adapters.restaurant import RestaurantBusinessAdapter  # noqa: E402
from abis_grp_runtime.connectors.authorized_http_sandbox import AuthorizedHttpSandboxConnector  # noqa: E402
from abis_grp_runtime.connectors.non_production_egress import EnvironmentClassification  # noqa: E402
from abis_grp_runtime.e2e.service import GrokE2EService  # noqa: E402
from abis_grp_runtime.execution import ExecutionClass, resolve_execution_disposition  # noqa: E402
from abis_grp_runtime.gateway.execution_surface import find_advertised_interaction  # noqa: E402
from abis_grp_runtime.gateway.preflight import (  # noqa: E402
    PREFLIGHT_ADAPTER_NOT_CONFIGURED,
    PREFLIGHT_READY,
    evaluate_preflight,
)
from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.adapters.shopping import ShoppingBusinessAdapter  # noqa: E402
from abis_grp_runtime.gateway.execution_surface import _refresh_aliases  # noqa: E402
from abis_grp_runtime.registry.factory import build_reference_registry  # noqa: E402
from abis_grp_runtime.registry.interaction_registry import (  # noqa: E402
    BusinessAdapterRegistration,
    RuntimeInteractionRegistry,
    set_active_registry,
)
from crs.engine import ReservationEngine  # noqa: E402
from css.engine import CommerceEngine  # noqa: E402
from scripts.mock_restaurant_http_server import MockRestaurantHandler  # noqa: E402


class AuthorizedHttpRestaurantTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._mock_httpd: HTTPServer | None = None
        self._mock_thread: threading.Thread | None = None
        self._mock_port = 0

    def tearDown(self) -> None:
        if self._mock_httpd:
            self._mock_httpd.shutdown()
        if self._mock_thread:
            self._mock_thread.join(timeout=2)
        self._tmp.cleanup()
        for key in (
            "ABIS_RESTAURANT_HTTP_ADAPTER_ENABLED",
            "ABIS_RESTAURANT_HTTP_ADAPTER_BASE_URL",
            "ABIS_RESTAURANT_HTTP_ADAPTER_PATH",
            "ABIS_RESTAURANT_HTTP_ADAPTER_ENV",
            "ABIS_RESTAURANT_HTTP_ADAPTER_ALLOWLIST_ID",
        ):
            os.environ.pop(key, None)

    def _start_mock_server(self) -> int:
        self._mock_httpd = HTTPServer(("127.0.0.1", 0), MockRestaurantHandler)
        self._mock_port = self._mock_httpd.server_address[1]
        self._mock_thread = threading.Thread(target=self._mock_httpd.serve_forever, daemon=True)
        self._mock_thread.start()
        return self._mock_port

    def _http_config(self, port: int) -> RestaurantHttpAdapterConfig:
        return RestaurantHttpAdapterConfig(
            enabled=True,
            adapter_id="restaurant-http-sandbox-test",
            allowlist_id="test-local-mock-v1",
            base_url=f"http://127.0.0.1:{port}",
            allowed_paths=("/sandbox/v1/reservations",),
            environment_classification=EnvironmentClassification.MOCK,
            timeout_seconds=3.0,
            max_response_bytes=65536,
            mapping_version="1",
        )

    def _registry(self, port: int) -> Any:
        crs = ReservationEngine(data_dir=self._tmp.name)
        css = CommerceEngine()
        adapter = RestaurantBusinessAdapter(crs, http_adapter_config=self._http_config(port))
        registry = RuntimeInteractionRegistry()
        registry.register(BusinessAdapterRegistration(adapter=adapter, operation="reserve", published=True))
        registry.register(
            BusinessAdapterRegistration(
                adapter=ShoppingBusinessAdapter(css),
                operation="submit_order",
                published=True,
            )
        )
        set_active_registry(registry)
        _refresh_aliases()
        return registry

    def test_real_external_still_denied(self) -> None:
        disp = resolve_execution_disposition(ExecutionClass.REAL_EXTERNAL)
        self.assertFalse(disp.allowed)

    def test_authorized_non_production_allowed(self) -> None:
        disp = resolve_execution_disposition(ExecutionClass.AUTHORIZED_NON_PRODUCTION)
        self.assertTrue(disp.allowed)

    def test_shopping_does_not_advertise_external_class(self) -> None:
        entry = find_advertised_interaction("shopping", "submit_order")
        self.assertIsNotNone(entry)
        self.assertNotIn("AUTHORIZED_NON_PRODUCTION", entry.execution_classes_allowed)

    def test_provenance_not_in_native_payload(self) -> None:
        port = self._start_mock_server()
        connector = AuthorizedHttpSandboxConnector(self._http_config(port))
        result = connector.execute(
            "reserve",
            {
                "date": "2026-09-12",
                "time": "20:00",
                "party_size": 2,
                "seating_type": "TABLE",
                "idempotency_key": "idem-1",
            },
        )
        meta = connector.consume_execution_metadata()
        self.assertTrue(meta.get("external_request_attempted"))
        self.assertTrue(meta.get("external_response_received"))
        payload = dict(result.payload or {})
        for forbidden in (
            "adapter_id",
            "egress_verdict",
            "allowlist_id",
            "environment_classification",
            "external_request_attempted",
        ):
            self.assertNotIn(forbidden, payload)

    def test_e2e_http_boundary_happy_path(self) -> None:
        port = self._start_mock_server()
        registry = self._registry(port)
        service = GrokE2EService(registry)
        config = GatewayConfig(bearer_token="test-token")

        preflight = evaluate_preflight(
            config,
            vertical="restaurant",
            operation="reserve",
            execution_class="AUTHORIZED_NON_PRODUCTION",
        )
        self.assertEqual(preflight["preflight_state"], PREFLIGHT_READY)

        payload = {
            "agent_id": "adapter-test-agent",
            "agent_type": "test",
            "operation": "reserve",
            "execution_class": "AUTHORIZED_NON_PRODUCTION",
            "authorization_token": "ALLOW",
            "correlation_id": "corr-http-001",
            "vertical": "restaurant",
            "input": {
                "date": "2026-09-12",
                "time": "19:00",
                "party_size": 3,
                "seating_type": "TABLE",
                "customer_reference": "TEST-CUST-HTTP-001",
                "idempotency_key": "idem-http-001",
            },
        }
        response = service.invoke_from_dict(payload)
        body = response.to_dict()
        self.assertEqual(body["transport_status"], "ACCEPTED")
        native = body.get("native_result") or {}
        self.assertEqual(native.get("external_status"), "CONFIRMED")
        self.assertTrue(str(native.get("external_identifier") or "").startswith("MOCK-RSV-"))
        provenance = body.get("execution_provenance") or {}
        self.assertEqual(
            (provenance.get("connector") or {}).get("kind"),
            "authorized_http_sandbox",
        )
        self.assertTrue(provenance.get("external_request_attempted"))
        self.assertTrue(provenance.get("external_response_received"))
        self.assertNotIn("Authorization", json.dumps(provenance))
        outcome = body.get("outcome_disposition") or {}
        self.assertEqual(outcome.get("disposition"), "NOT_EVALUATED")
        self.assertTrue(body.get("trace_reference"))

    def test_preflight_adapter_not_configured_without_env(self) -> None:
        crs = ReservationEngine(data_dir=self._tmp.name)
        css = CommerceEngine()
        build_reference_registry(crs, css)
        config = GatewayConfig(bearer_token="test-token")
        body = evaluate_preflight(
            config,
            vertical="restaurant",
            operation="reserve",
            execution_class="AUTHORIZED_NON_PRODUCTION",
        )
        self.assertEqual(body["preflight_state"], PREFLIGHT_ADAPTER_NOT_CONFIGURED)

    def test_connector_egress_denied_bad_base(self) -> None:
        bad = self._http_config(9095)
        bad = RestaurantHttpAdapterConfig(
            enabled=bad.enabled,
            adapter_id=bad.adapter_id,
            allowlist_id=bad.allowlist_id,
            base_url="http://192.168.1.50:8080",
            allowed_paths=bad.allowed_paths,
            environment_classification=bad.environment_classification,
            timeout_seconds=bad.timeout_seconds,
            max_response_bytes=bad.max_response_bytes,
            mapping_version=bad.mapping_version,
        )
        connector = AuthorizedHttpSandboxConnector(bad)
        result = connector.execute("reserve", {"date": "x", "time": "y", "party_size": 1, "seating_type": "T"})
        self.assertEqual((result.error or {}).get("code"), "EGRESS_DENIED")


if __name__ == "__main__":
    unittest.main()
