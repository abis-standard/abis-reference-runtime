"""C3-04A — sanitized HBX external failure observability (mock transport only)."""

from __future__ import annotations

import json
import ssl
import tempfile
import unittest
from unittest import mock

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.connectors.authorized_mtls_sandbox import AuthorizedMtlsSandboxConnector  # noqa: E402
from abis_grp_runtime.connectors.providers.hbx_external_observability import (  # noqa: E402
    ERROR_CATEGORY_AUTH_REJECTION,
    ERROR_CATEGORY_MALFORMED_EXTERNAL_RESPONSE,
    ERROR_CATEGORY_PROVIDER_HTTP_REJECTION,
    ERROR_CATEGORY_PROVIDER_SERVER_ERROR,
    ERROR_CATEGORY_RESPONSE_MAPPING_FAILURE,
)
from abis_grp_runtime.e2e.service import GrokE2EService  # noqa: E402
from abis_grp_runtime.gateway.evidence_log import append_evidence  # noqa: E402
from abis_grp_runtime.registry.factory import build_reference_registry  # noqa: E402
from abis_grp_runtime.adapters.travel import TravelStayReserveAdapter  # noqa: E402
from crs.engine import ReservationEngine  # noqa: E402
from css.engine import CommerceEngine  # noqa: E402
from tests._hbx_test_helpers import (  # noqa: E402
    SENSITIVE_BOOKING_REF,
    SYNTHETIC_OPAQUE_OFFER,
    TEST_API_SECRET,
    load_hbx_fixture,
    synthetic_hbx_config,
    synthetic_stay_reserve_context,
)
from tests.test_authorized_mtls_sandbox import _NetworkTripwire, _mock_https_success  # noqa: E402


def _mock_http(status: int, body: bytes, content_type: str = "application/json"):
    def _post(*args, **kwargs):  # noqa: ANN002, ANN003
        return status, body, content_type

    return _post


class HbxFailureObservabilityTestCase(unittest.TestCase):
    def _run_connector(self, https_post) -> tuple:  # noqa: ANN001
        with tempfile.TemporaryDirectory() as tmp:
            cfg = synthetic_hbx_config(tmp)
            connector = AuthorizedMtlsSandboxConnector(
                cfg, https_post=https_post, unix_timestamp=1_700_000_000
            )
            with _NetworkTripwire(), mock.patch(
                "abis_grp_runtime.connectors.authorized_mtls_sandbox.build_client_mtls_context",
                return_value=ssl.create_default_context(),
            ):
                native = connector.execute("stay_reserve", synthetic_stay_reserve_context())
            return native, connector.consume_execution_metadata()

    def _assert_common_failure_observability(self, meta: dict, *, http_status: int, error_code: str, category: str) -> None:
        ext = meta.get("external_execution") or {}
        self.assertEqual(ext.get("http_status"), http_status)
        self.assertEqual(ext.get("error_code"), error_code)
        self.assertEqual(ext.get("error_category"), category)
        self.assertTrue(meta.get("external_request_attempted"))
        self.assertTrue(meta.get("external_response_received"))
        self.assertNotIn(SENSITIVE_BOOKING_REF, json.dumps(meta))
        self.assertNotIn(SYNTHETIC_OPAQUE_OFFER, json.dumps(meta))
        self.assertNotIn(TEST_API_SECRET, json.dumps(meta))

    def test_http_401(self) -> None:
        native, meta = self._run_connector(_mock_http(401, b"{}"))
        self.assertEqual(native.error.get("code"), "AUTH_REJECTED")
        self._assert_common_failure_observability(
            meta, http_status=401, error_code="AUTH_REJECTED", category=ERROR_CATEGORY_AUTH_REJECTION
        )
        self.assertEqual(meta["external_execution"].get("http_status_class"), "4XX")

    def test_http_403(self) -> None:
        native, meta = self._run_connector(_mock_http(403, b"{}"))
        self.assertEqual(native.error.get("code"), "AUTH_REJECTED")
        self._assert_common_failure_observability(
            meta, http_status=403, error_code="AUTH_REJECTED", category=ERROR_CATEGORY_AUTH_REJECTION
        )

    def test_http_400(self) -> None:
        native, meta = self._run_connector(_mock_http(400, b"{}"))
        self.assertEqual(native.error.get("code"), "HTTP_4XX")
        self._assert_common_failure_observability(
            meta,
            http_status=400,
            error_code="HTTP_4XX",
            category=ERROR_CATEGORY_PROVIDER_HTTP_REJECTION,
        )

    def test_http_422(self) -> None:
        native, meta = self._run_connector(_mock_http(422, b"{}"))
        self.assertEqual(native.error.get("code"), "HTTP_4XX")
        self._assert_common_failure_observability(
            meta,
            http_status=422,
            error_code="HTTP_4XX",
            category=ERROR_CATEGORY_PROVIDER_HTTP_REJECTION,
        )

    def test_http_500(self) -> None:
        native, meta = self._run_connector(_mock_http(500, b"{}"))
        self.assertEqual(native.error.get("code"), "HTTP_5XX")
        self._assert_common_failure_observability(
            meta,
            http_status=500,
            error_code="HTTP_5XX",
            category=ERROR_CATEGORY_PROVIDER_SERVER_ERROR,
        )
        self.assertEqual(meta["external_execution"].get("http_status_class"), "5XX")

    def test_http_200_malformed_json(self) -> None:
        native, meta = self._run_connector(_mock_http(200, b"not-json"))
        self.assertEqual(native.error.get("code"), "MALFORMED_EXTERNAL_RESPONSE")
        ext = meta["external_execution"]
        self.assertEqual(ext.get("http_status"), 200)
        self.assertEqual(ext.get("http_status_class"), "2XX")
        self.assertEqual(ext.get("error_category"), ERROR_CATEGORY_MALFORMED_EXTERNAL_RESPONSE)
        self.assertFalse(ext.get("response_json_parse_succeeded"))
        self.assertFalse(ext.get("response_mapping_succeeded"))

    def test_http_200_mapping_failure(self) -> None:
        native, meta = self._run_connector(_mock_http(200, b"{}"))
        self.assertEqual(native.error.get("code"), "RESPONSE_MAPPING_FAILED")
        ext = meta["external_execution"]
        self.assertEqual(ext.get("error_category"), ERROR_CATEGORY_RESPONSE_MAPPING_FAILURE)
        self.assertTrue(ext.get("response_json_parse_succeeded"))
        self.assertFalse(ext.get("response_mapping_succeeded"))

    def test_http_200_success_fixture(self) -> None:
        fixture = load_hbx_fixture("booking_confirmed_success.json")
        fixture["booking"]["reference"] = SENSITIVE_BOOKING_REF
        native, meta = self._run_connector(_mock_https_success(fixture))
        self.assertEqual(native.technical_status, "TRANSPORT_OK")
        ext = meta["external_execution"]
        self.assertEqual(ext.get("http_status"), 200)
        self.assertNotIn("error_code", ext)
        self.assertTrue(ext.get("response_mapping_succeeded"))
        self.assertTrue(ext.get("provider_native_status_present"))
        self.assertTrue(ext.get("external_identifier_present"))
        self.assertNotIn(SENSITIVE_BOOKING_REF, json.dumps(meta))

    def test_service_invoke_preserves_not_evaluated_and_observability(self) -> None:
        fixture = load_hbx_fixture("booking_confirmed_success.json")

        def _401(*args, **kwargs):  # noqa: ANN002, ANN003
            return 401, b"{}", "application/json"

        with tempfile.TemporaryDirectory() as tmp:
            cfg = synthetic_hbx_config(tmp)
            connector = AuthorizedMtlsSandboxConnector(
                cfg, https_post=_401, unix_timestamp=1_700_000_000
            )
            adapter = TravelStayReserveAdapter(hbx_mtls_connector=connector, hbx_mtls_config=cfg)
            registry = build_reference_registry(ReservationEngine(data_dir=tmp), CommerceEngine())
            registry._entries[("travel", "stay_reserve")] = (
                adapter,
                registry._entries[("travel", "stay_reserve")][1],
            )
            service = GrokE2EService(registry)
            from abis_grp_runtime.agent.envelope import AgentRequestEnvelope

            request = AgentRequestEnvelope(
                agent_id="c3-04a-agent",
                agent_type="reference-agent",
                operation="stay_reserve",
                execution_class="AUTHORIZED_NON_PRODUCTION",
                authorization_token="ALLOW",
                correlation_id="c3-04a-observability-001",
                structured_input=synthetic_stay_reserve_context(),
                metadata={"vertical": "travel"},
            )
            with _NetworkTripwire(), mock.patch(
                "abis_grp_runtime.connectors.authorized_mtls_sandbox.build_client_mtls_context",
                return_value=ssl.create_default_context(),
            ):
                response = service.invoke(request)
            self.assertEqual((response.outcome_disposition or {}).get("disposition"), "NOT_EVALUATED")
            provenance = response.execution_provenance or {}
            ext = provenance.get("external_execution") or {}
            self.assertEqual(ext.get("http_status"), 401)
            self.assertEqual(ext.get("error_code"), "AUTH_REJECTED")

    def test_gateway_evidence_includes_sanitized_failure_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/evidence.jsonl"
            append_evidence(
                path,
                {
                    "vertical": "travel",
                    "execution_disposition": "AUTHORIZED_NON_PRODUCTION",
                    "http_status": 422,
                    "http_status_class": "4XX",
                    "error_code": "HTTP_4XX",
                    "error_category": "PROVIDER_HTTP_REJECTION",
                    "external_identifier_present": False,
                    "response_json_parse_succeeded": False,
                },
            )
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            self.assertIn("error_code", text)
            self.assertIn("PROVIDER_HTTP_REJECTION", text)
            self.assertNotIn(SENSITIVE_BOOKING_REF, text)


if __name__ == "__main__":
    unittest.main()
