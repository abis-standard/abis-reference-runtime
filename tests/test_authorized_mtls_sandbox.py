"""Authorized mTLS sandbox connector — mock transport only (C2)."""

from __future__ import annotations

import json
import socket
import ssl
import tempfile
import unittest
from unittest import mock

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.adapters.hbx_test_adapter_config import HbxTestMtlsAdapterConfig  # noqa: E402
from abis_grp_runtime.adapters.travel import TravelStayReserveAdapter  # noqa: E402
from abis_grp_runtime.connectors.authorized_mtls_sandbox import AuthorizedMtlsSandboxConnector  # noqa: E402
from abis_grp_runtime.connectors.bound_https_transport import InsecureTlsContextError, require_secure_tls_context  # noqa: E402
from abis_grp_runtime.connectors.mtls_ssl_context import build_client_mtls_context  # noqa: E402
from abis_grp_runtime.connectors.non_production_egress import NonProductionEgressPolicy  # noqa: E402
from abis_grp_runtime.connectors.providers.hbx_test_booking import HBX_TEST_AUTHORIZED_BOOKING_PATH  # noqa: E402
from abis_grp_runtime.e2e.service import GrokE2EService  # noqa: E402
from abis_grp_runtime.gateway.evidence_log import append_evidence  # noqa: E402
from abis_grp_runtime.gateway.preflight import (  # noqa: E402
    PREFLIGHT_ADAPTER_NOT_CONFIGURED,
    PREFLIGHT_READY,
    evaluate_preflight,
    evaluate_travel_hbx_preflight,
)
from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.registry.factory import build_reference_registry  # noqa: E402
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


class _NetworkTripwire:
    def __enter__(self) -> None:
        self._patch = mock.patch(
            "socket.create_connection",
            side_effect=AssertionError("unexpected real network connection"),
        )
        self._patch.start()

    def __exit__(self, *args: object) -> None:
        self._patch.stop()


def _mock_https_success(fixture: dict) -> object:
    def _post(destination, path, headers, body, timeout, max_response_bytes, ssl_context):  # noqa: ANN001
        payload = json.loads(body.decode())
        self_assert = payload["rooms"][0]["rateKey"]
        if self_assert != SYNTHETIC_OPAQUE_OFFER:
            raise AssertionError("opaque offer not preserved in provider request")
        assert "Api-key" in headers
        assert "X-Signature" in headers
        assert SYNTHETIC_OPAQUE_OFFER not in json.dumps(headers)
        return 200, json.dumps(fixture).encode(), "application/json"

    return _post


class MtlsSslContextTestCase(unittest.TestCase):
    def test_rejects_insecure_context(self) -> None:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        with self.assertRaises(InsecureTlsContextError):
            require_secure_tls_context(ctx)

    def test_build_client_mtls_invokes_load_cert_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = synthetic_hbx_config(tmp)
            ctx = ssl.create_default_context()
            with mock.patch.object(ssl.SSLContext, "load_cert_chain") as load_chain:
                build_client_mtls_context(
                    certificate_path=cfg.client_certificate_path,
                    private_key_path=cfg.encrypted_private_key_path,
                    passphrase_provider=lambda: "TEST-PASSPHRASE-SYNTHETIC",
                    base_context=ctx,
                )
                load_chain.assert_called_once()
                self.assertTrue(ctx.check_hostname)
                self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)


class HbxConfigValidationTestCase(unittest.TestCase):
    def test_production_hostname_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = synthetic_hbx_config(tmp, hostname="api.hotelbeds.com")
            self.assertFalse(cfg.structurally_valid())

    def test_wrong_path_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = synthetic_hbx_config(tmp, allowed_paths=("/hotel-api/1.0/other",))
            self.assertFalse(cfg.structurally_valid())


class AuthorizedMtlsConnectorTestCase(unittest.TestCase):
    def test_success_mock_transport(self) -> None:
        fixture = load_hbx_fixture("booking_confirmed_success.json")
        fixture["booking"]["reference"] = SENSITIVE_BOOKING_REF
        with tempfile.TemporaryDirectory() as tmp:
            cfg = synthetic_hbx_config(tmp)
            connector = AuthorizedMtlsSandboxConnector(
                cfg,
                https_post=_mock_https_success(fixture),
                unix_timestamp=1_700_000_000,
            )
            with _NetworkTripwire(), mock.patch(
                "abis_grp_runtime.connectors.authorized_mtls_sandbox.build_client_mtls_context",
                return_value=ssl.create_default_context(),
            ):
                native = connector.execute("stay_reserve", synthetic_stay_reserve_context())
            self.assertEqual(native.technical_status, "TRANSPORT_OK")
            self.assertEqual(native.external_status, "CONFIRMED")
            self.assertEqual(native.external_identifier, SENSITIVE_BOOKING_REF)
            meta = connector.consume_execution_metadata()
            self.assertTrue(meta["external_request_attempted"])
            self.assertEqual(meta["business_outcome"], "NOT_EVALUATED")
            self.assertNotIn(TEST_API_SECRET, json.dumps(meta))

    def test_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = synthetic_hbx_config(tmp)

            def _bad_post(*args, **kwargs):  # noqa: ANN002, ANN003
                return 200, b"not-json", "application/json"

            connector = AuthorizedMtlsSandboxConnector(cfg, https_post=_bad_post, unix_timestamp=1)
            with _NetworkTripwire(), mock.patch(
                "abis_grp_runtime.connectors.authorized_mtls_sandbox.build_client_mtls_context",
                return_value=ssl.create_default_context(),
            ):
                native = connector.execute("stay_reserve", synthetic_stay_reserve_context())
            self.assertEqual(native.technical_status, "TRANSPORT_FAILED")

    def test_oversized_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = synthetic_hbx_config(tmp)

            def _big_post(*args, **kwargs):  # noqa: ANN002, ANN003
                return 200, b"x" * (cfg.max_response_bytes + 1), "application/json"

            connector = AuthorizedMtlsSandboxConnector(cfg, https_post=_big_post, unix_timestamp=1)
            with _NetworkTripwire(), mock.patch(
                "abis_grp_runtime.connectors.authorized_mtls_sandbox.build_client_mtls_context",
                return_value=ssl.create_default_context(),
            ):
                native = connector.execute("stay_reserve", synthetic_stay_reserve_context())
            self.assertEqual(native.technical_status, "TRANSPORT_FAILED")

    def test_redirect_denied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = synthetic_hbx_config(tmp)

            def _redirect(*args, **kwargs):  # noqa: ANN002, ANN003
                return 302, b"", "application/json"

            connector = AuthorizedMtlsSandboxConnector(cfg, https_post=_redirect, unix_timestamp=1)
            with _NetworkTripwire(), mock.patch(
                "abis_grp_runtime.connectors.authorized_mtls_sandbox.build_client_mtls_context",
                return_value=ssl.create_default_context(),
            ):
                native = connector.execute("stay_reserve", synthetic_stay_reserve_context())
            self.assertEqual(native.error.get("code"), "REDIRECT_DENIED")

    def test_provider_auth_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = synthetic_hbx_config(tmp)

            def _401(*args, **kwargs):  # noqa: ANN002, ANN003
                return 401, b"{}", "application/json"

            connector = AuthorizedMtlsSandboxConnector(cfg, https_post=_401, unix_timestamp=1)
            with _NetworkTripwire(), mock.patch(
                "abis_grp_runtime.connectors.authorized_mtls_sandbox.build_client_mtls_context",
                return_value=ssl.create_default_context(),
            ):
                native = connector.execute("stay_reserve", synthetic_stay_reserve_context())
            self.assertEqual(native.error.get("code"), "AUTH_REJECTED")

    def test_booking_path_independent_of_allowlist_order(self) -> None:
        fixture = load_hbx_fixture("booking_confirmed_success.json")
        captured_paths: list[str] = []

        def _capture_post(destination, path, headers, body, timeout, max_response_bytes, ssl_context):  # noqa: ANN001
            captured_paths.append(path)
            return _mock_https_success(fixture)(
                destination, path, headers, body, timeout, max_response_bytes, ssl_context
            )

        with tempfile.TemporaryDirectory() as tmp:
            decoy = "/hotel-api/1.0/decoy-path-synthetic"
            cfg = synthetic_hbx_config(
                tmp,
                allowed_paths=(decoy, HBX_TEST_AUTHORIZED_BOOKING_PATH),
            )
            self.assertIn(HBX_TEST_AUTHORIZED_BOOKING_PATH, cfg.allowed_paths)
            connector = AuthorizedMtlsSandboxConnector(
                cfg,
                https_post=_capture_post,
                unix_timestamp=1_700_000_000,
            )
            with _NetworkTripwire(), mock.patch(
                "abis_grp_runtime.connectors.authorized_mtls_sandbox.build_client_mtls_context",
                return_value=ssl.create_default_context(),
            ):
                native = connector.execute("stay_reserve", synthetic_stay_reserve_context())
            self.assertEqual(native.technical_status, "TRANSPORT_OK")
            self.assertEqual(captured_paths, [HBX_TEST_AUTHORIZED_BOOKING_PATH])

    def test_booking_path_missing_from_allowlist_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = synthetic_hbx_config(
                tmp,
                allowed_paths=("/hotel-api/1.0/decoy-only-synthetic",),
            )
            self.assertFalse(cfg.structurally_valid())
            connector = AuthorizedMtlsSandboxConnector(cfg, unix_timestamp=1)
            native = connector.execute("stay_reserve", synthetic_stay_reserve_context())
            self.assertEqual(native.technical_status, "TRANSPORT_FAILED")
            self.assertEqual(native.error.get("code"), "ADAPTER_NOT_CONFIGURED")

    def test_egress_denies_non_booking_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = synthetic_hbx_config(tmp)
            policy = NonProductionEgressPolicy(
                allowlist_id=cfg.allowlist_id,
                target_mode=cfg.target_mode,
                authorized_hostname=cfg.authorized_hostname,
                authorized_port=cfg.authorized_port,
                allowed_paths=("/hotel-api/1.0/bookings",),
                environment_classification=cfg.environment_classification,
                target_authorization_id=cfg.target_authorization_id,
                resolve_fn=lambda _h, _p: ("203.0.113.10",),
            )
            connector = AuthorizedMtlsSandboxConnector(
                cfg,
                policy=policy,
                https_post=_mock_https_success(load_hbx_fixture("booking_confirmed_success.json")),
                unix_timestamp=1,
            )
            destination, verdict = policy.resolve_validated_destination("/hotel-api/1.0/availability")
            self.assertIsNone(destination)
            self.assertEqual(verdict.decision.value, "DENY")


class TravelHbxIntegrationTestCase(unittest.TestCase):
    def test_service_invoke_not_evaluated(self) -> None:
        fixture = load_hbx_fixture("booking_confirmed_success.json")
        with tempfile.TemporaryDirectory() as tmp:
            cfg = synthetic_hbx_config(tmp)
            connector = AuthorizedMtlsSandboxConnector(
                cfg,
                https_post=_mock_https_success(fixture),
                unix_timestamp=1_700_000_000,
            )
            adapter = TravelStayReserveAdapter(hbx_mtls_connector=connector, hbx_mtls_config=cfg)
            registry = build_reference_registry(ReservationEngine(data_dir=tmp), CommerceEngine())
            registry._entries[("travel", "stay_reserve")] = (adapter, registry._entries[("travel", "stay_reserve")][1])
            service = GrokE2EService(registry)
            from abis_grp_runtime.agent.envelope import AgentRequestEnvelope

            request = AgentRequestEnvelope(
                agent_id="c2-agent",
                agent_type="reference-agent",
                operation="stay_reserve",
                execution_class="AUTHORIZED_NON_PRODUCTION",
                authorization_token="ALLOW",
                correlation_id="c2-hbx-001",
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
            self.assertNotIn(SYNTHETIC_OPAQUE_OFFER, json.dumps(provenance))
            self.assertNotIn("TEST_API_SECRET", json.dumps(provenance))

    def test_preflight_ready_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = synthetic_hbx_config(tmp)
            adapter = TravelStayReserveAdapter(hbx_mtls_config=cfg)
            self.assertIsNone(evaluate_travel_hbx_preflight(adapter))

    def test_preflight_not_configured_default_registry(self) -> None:
        build_reference_registry(ReservationEngine(data_dir=tempfile.mkdtemp()), CommerceEngine())
        body = evaluate_preflight(
            GatewayConfig(host="127.0.0.1", port=0),
            vertical="travel",
            operation="stay_reserve",
            execution_class="AUTHORIZED_NON_PRODUCTION",
        )
        self.assertEqual(body["preflight_state"], PREFLIGHT_ADAPTER_NOT_CONFIGURED)

    def test_evidence_redacts_booking_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence_path = f"{tmp}/evidence.jsonl"
            append_evidence(
                evidence_path,
                {
                    "vertical": "travel",
                    "execution_disposition": "AUTHORIZED_NON_PRODUCTION",
                    "external_identifier_present": True,
                },
            )
            text = open(evidence_path, encoding="utf-8").read()
            self.assertNotIn(SENSITIVE_BOOKING_REF, text)
            self.assertIn("external_identifier_present", text)


if __name__ == "__main__":
    unittest.main()
