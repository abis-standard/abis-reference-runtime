"""D-11B-04 security matrix — authorized remote sandbox HTTPS boundary."""

from __future__ import annotations

import json
import os
import socket
import ssl
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from unittest import mock

from tests._bootstrap import ensure_paths

ensure_paths()
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from abis_grp_runtime.adapters.http_adapter_config import RestaurantHttpAdapterConfig  # noqa: E402
from abis_grp_runtime.adapters.restaurant import RestaurantBusinessAdapter  # noqa: E402
from abis_grp_runtime.connectors.authorized_http_sandbox import AuthorizedHttpSandboxConnector  # noqa: E402
from abis_grp_runtime.connectors.non_production_egress import (  # noqa: E402
    EnvironmentClassification,
    NonProductionEgressPolicy,
    TargetMode,
)
from abis_grp_runtime.e2e.service import GrokE2EService  # noqa: E402
from abis_grp_runtime.execution import ExecutionClass, resolve_execution_disposition  # noqa: E402
from abis_grp_runtime.gateway.execution_surface import find_advertised_interaction  # noqa: E402
from abis_grp_runtime.gateway.preflight import evaluate_preflight  # noqa: E402
from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.registry.interaction_registry import (  # noqa: E402
    BusinessAdapterRegistration,
    RuntimeInteractionRegistry,
    set_active_registry,
)
from crs.engine import ReservationEngine  # noqa: E402
from scripts.mock_restaurant_http_server import MockRestaurantHandler  # noqa: E402


def _remote_config(
    *,
    hostname: str = "sandbox.example.test",
    port: int = 443,
    credential_env: str = "ABIS_TEST_REMOTE_CRED",
    resolve_fn: Any = None,
    ssl_context_factory: Any = None,
    **kwargs: Any,
) -> tuple[RestaurantHttpAdapterConfig, AuthorizedHttpSandboxConnector, NonProductionEgressPolicy]:
    defaults: dict[str, Any] = {
        "enabled": True,
        "adapter_id": "restaurant-http-remote-test",
        "allowlist_id": "remote-sandbox-v1",
        "target_mode": TargetMode.REMOTE_AUTHORIZED,
        "target_authorization_id": "remote-authz-001",
        "authorized_hostname": hostname,
        "authorized_port": port,
        "base_url": f"https://{hostname}" if port == 443 else f"https://{hostname}:{port}",
        "allowed_paths": ("/sandbox/v1/reservations",),
        "environment_classification": EnvironmentClassification.SANDBOX,
        "timeout_seconds": 5.0,
        "max_response_bytes": 65536,
        "max_request_body_bytes": 16384,
        "mapping_version": "1",
        "credential_env_var": credential_env,
    }
    defaults.update(kwargs)
    defaults.pop("ssl_context_factory", None)
    cfg = RestaurantHttpAdapterConfig(**defaults)
    policy_kwargs = {
        "allowlist_id": cfg.allowlist_id,
        "target_mode": cfg.target_mode,
        "authorized_hostname": cfg.authorized_hostname,
        "authorized_port": cfg.authorized_port,
        "allowed_paths": cfg.allowed_paths,
        "environment_classification": cfg.environment_classification,
        "target_authorization_id": cfg.target_authorization_id,
        "base_url": cfg.base_url,
    }
    if resolve_fn is not None:
        policy_kwargs["resolve_fn"] = resolve_fn
    policy = NonProductionEgressPolicy(**policy_kwargs)
    connector = AuthorizedHttpSandboxConnector(
        cfg,
        policy=policy,
        ssl_context_factory=ssl_context_factory,
    )
    return cfg, connector, policy


class _TlsMockHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_POST(self) -> None:
        if self.path != "/sandbox/v1/reservations":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", "0"))
        _ = self.rfile.read(length)
        body = json.dumps(
            {
                "mock_reservation_id": "MOCK-RSV-REMOTE-001",
                "native_status": "CONFIRMED",
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class _RedirectHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_POST(self) -> None:
        self.send_response(302)
        self.send_header("Location", "https://evil.example/steal")
        self.end_headers()


_FIXTURE_TLS_DIR = Path(__file__).resolve().parent / "fixtures" / "tls"


def _fixture_cert(hostname: str) -> tuple[str, str]:
    if hostname == "sandbox.example.test":
        return (
            str(_FIXTURE_TLS_DIR / "sandbox.example.test.pem"),
            str(_FIXTURE_TLS_DIR / "sandbox.example.test.key"),
        )
    return (
        str(_FIXTURE_TLS_DIR / "other.example.pem"),
        str(_FIXTURE_TLS_DIR / "other.example.key"),
    )


class D11B04SecurityMatrixTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._results: dict[str, str] = {}
        os.environ["ABIS_TEST_REMOTE_CRED"] = "test-token-secret"

    def tearDown(self) -> None:
        self._tmp.cleanup()
        os.environ.pop("ABIS_TEST_REMOTE_CRED", None)

    def _record(self, case_id: str, passed: bool) -> None:
        self._results[case_id] = "PASS" if passed else "FAIL"

    def _reserve_ctx(self) -> dict[str, Any]:
        return {
            "date": "2026-09-12",
            "time": "20:00",
            "party_size": 2,
            "seating_type": "TABLE",
            "idempotency_key": "idem-remote",
        }

    def test_01_localhost_mock_allow(self) -> None:
        httpd = HTTPServer(("127.0.0.1", 0), MockRestaurantHandler)
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            cfg = RestaurantHttpAdapterConfig(
                enabled=True,
                adapter_id="local",
                allowlist_id="local",
                target_mode=TargetMode.LOCALHOST_MOCK,
                target_authorization_id="local",
                authorized_hostname="127.0.0.1",
                authorized_port=port,
                base_url=f"http://127.0.0.1:{port}",
                allowed_paths=("/sandbox/v1/reservations",),
                environment_classification=EnvironmentClassification.MOCK,
                timeout_seconds=3.0,
                max_response_bytes=65536,
                max_request_body_bytes=16384,
                mapping_version="1",
            )
            result = AuthorizedHttpSandboxConnector(cfg).execute("reserve", self._reserve_ctx())
            ok = result.technical_status == "TRANSPORT_OK"
            self._record("01", ok)
            self.assertTrue(ok)
        finally:
            httpd.shutdown()
            thread.join(timeout=2)

    def test_02_authorized_remote_https_allow(self) -> None:
        hostname = "sandbox.example.test"
        public_ip = "93.184.216.34"
        cert_path, key_path = _fixture_cert(hostname)
        httpd = HTTPServer(("127.0.0.1", 0), _TlsMockHandler)
        local_port = httpd.server_address[1]
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()

        trust_ctx = ssl.create_default_context()
        trust_ctx.load_verify_locations(cert_path)

        def resolver(_h: str, _p: int) -> tuple[str, ...]:
            return (public_ip,)

        _real_create_connection = socket.create_connection

        def redirect_connection(address, *args, **kwargs):
            host, _port = address
            if host == public_ip:
                address = ("127.0.0.1", local_port)
            return _real_create_connection(address, *args, **kwargs)

        _, connector, _ = _remote_config(
            hostname=hostname,
            port=443,
            resolve_fn=resolver,
            ssl_context_factory=lambda: trust_ctx,
        )
        with mock.patch("abis_grp_runtime.connectors.bound_https_transport.socket.create_connection", redirect_connection):
            result = connector.execute("reserve", self._reserve_ctx())
        httpd.shutdown()
        thread.join(timeout=2)
        ok = result.technical_status == "TRANSPORT_OK"
        meta = connector.consume_execution_metadata()
        ok = ok and (meta.get("transport") or {}).get("tls") == "VERIFIED"
        self._record("02", ok)
        self.assertTrue(ok)

    def test_03_remote_http_deny(self) -> None:
        ok = False
        try:
            NonProductionEgressPolicy(
                allowlist_id="a",
                target_mode=TargetMode.REMOTE_AUTHORIZED,
                authorized_hostname="sandbox.example.test",
                authorized_port=443,
                allowed_paths=("/sandbox/v1/reservations",),
                environment_classification=EnvironmentClassification.SANDBOX,
                target_authorization_id="auth",
                base_url="http://sandbox.example.test",
            )
        except ValueError:
            ok = True
        self._record("03", ok)
        self.assertTrue(ok)

    def test_04_unlisted_hostname_deny(self) -> None:
        ok = False
        try:
            NonProductionEgressPolicy(
                allowlist_id="a",
                target_mode=TargetMode.REMOTE_AUTHORIZED,
                authorized_hostname="allowed.example",
                authorized_port=443,
                allowed_paths=("/sandbox/v1/reservations",),
                environment_classification=EnvironmentClassification.SANDBOX,
                target_authorization_id="auth",
                base_url="https://other.example",
            )
        except ValueError:
            ok = True
        self._record("04", ok)
        self.assertTrue(ok)

    def test_05_arbitrary_invoke_url_deny(self) -> None:
        from abis_grp_runtime.adapters._validation import reject_url_like_values
        from abis_grp_runtime.adapters.errors import AdapterValidationError

        ok = False
        try:
            reject_url_like_values({"date": "https://evil.example/x"})
        except AdapterValidationError:
            ok = True
        self._record("05", ok)
        self.assertTrue(ok)

    def test_06_rfc1918_deny(self) -> None:
        _, _, policy = _remote_config(resolve_fn=lambda _h, _p: ("192.168.0.5",))
        dest, verdict = policy.resolve_validated_destination("/sandbox/v1/reservations")
        ok = dest is None
        self._record("06", ok)
        self.assertTrue(ok)

    def test_07_loopback_remote_deny(self) -> None:
        policy = NonProductionEgressPolicy(
            allowlist_id="a",
            target_mode=TargetMode.REMOTE_AUTHORIZED,
            authorized_hostname="localhost",
            authorized_port=443,
            allowed_paths=("/sandbox/v1/reservations",),
            environment_classification=EnvironmentClassification.SANDBOX,
            target_authorization_id="auth",
            base_url="https://localhost",
            resolve_fn=lambda _h, _p: ("127.0.0.1",),
        )
        dest, _ = policy.resolve_validated_destination("/sandbox/v1/reservations")
        ok = dest is None
        self._record("07", ok)
        self.assertTrue(ok)

    def test_08_link_local_deny(self) -> None:
        _, _, policy = _remote_config(resolve_fn=lambda _h, _p: ("169.254.10.1",))
        dest, _ = policy.resolve_validated_destination("/sandbox/v1/reservations")
        self._record("08", dest is None)
        self.assertIsNone(dest)

    def test_09_metadata_ip_deny(self) -> None:
        _, _, policy = _remote_config(resolve_fn=lambda _h, _p: ("169.254.169.254",))
        dest, _ = policy.resolve_validated_destination("/sandbox/v1/reservations")
        self._record("09", dest is None)
        self.assertIsNone(dest)

    def test_10_ipv6_ula_deny(self) -> None:
        _, _, policy = _remote_config(resolve_fn=lambda _h, _p: ("fd00::1",))
        dest, _ = policy.resolve_validated_destination("/sandbox/v1/reservations")
        self._record("10", dest is None)
        self.assertIsNone(dest)

    def test_11_unauthorized_port_deny(self) -> None:
        ok = False
        try:
            NonProductionEgressPolicy(
                allowlist_id="a",
                target_mode=TargetMode.REMOTE_AUTHORIZED,
                authorized_hostname="sandbox.example.test",
                authorized_port=443,
                allowed_paths=("/sandbox/v1/reservations",),
                environment_classification=EnvironmentClassification.SANDBOX,
                target_authorization_id="auth",
                base_url="https://sandbox.example.test:8443",
            )
        except ValueError:
            ok = True
        self._record("11", ok)
        self.assertTrue(ok)

    def test_12_unauthorized_path_deny(self) -> None:
        _, _, policy = _remote_config()
        dest, _ = policy.resolve_validated_destination("/other")
        self._record("12", dest is None)
        self.assertIsNone(dest)

    def test_13_traversal_path_deny(self) -> None:
        _, _, policy = _remote_config()
        dest, _ = policy.resolve_validated_destination("/sandbox/v1/../secrets")
        self._record("13", dest is None)
        self.assertIsNone(dest)

    def test_14_redirect_deny(self) -> None:
        httpd = HTTPServer(("127.0.0.1", 0), _RedirectHandler)
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        cfg = RestaurantHttpAdapterConfig(
            enabled=True,
            adapter_id="local",
            allowlist_id="local",
            target_mode=TargetMode.LOCALHOST_MOCK,
            target_authorization_id="local",
            authorized_hostname="127.0.0.1",
            authorized_port=port,
            base_url=f"http://127.0.0.1:{port}",
            allowed_paths=("/sandbox/v1/reservations",),
            environment_classification=EnvironmentClassification.MOCK,
            timeout_seconds=3.0,
            max_response_bytes=65536,
            max_request_body_bytes=16384,
            mapping_version="1",
        )
        result = AuthorizedHttpSandboxConnector(cfg).execute("reserve", self._reserve_ctx())
        httpd.shutdown()
        thread.join(timeout=2)
        ok = (result.error or {}).get("code") == "NETWORK_ERROR"
        self._record("14", ok)
        self.assertTrue(ok)

    def test_15_invalid_tls_deny(self) -> None:
        hostname = "sandbox.example.test"
        public_ip = "93.184.216.34"
        cert_path, key_path = _fixture_cert(hostname)
        httpd = HTTPServer(("127.0.0.1", 0), _TlsMockHandler)
        local_port = httpd.server_address[1]
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        _, connector, _ = _remote_config(hostname=hostname, resolve_fn=lambda _h, _p: (public_ip,))

        _real_create_connection = socket.create_connection

        def redirect_connection(address, *args, **kwargs):
            host, _port = address
            if host == public_ip:
                address = ("127.0.0.1", local_port)
            return _real_create_connection(address, *args, **kwargs)

        with mock.patch("abis_grp_runtime.connectors.bound_https_transport.socket.create_connection", redirect_connection):
            result = connector.execute("reserve", self._reserve_ctx())
        httpd.shutdown()
        thread.join(timeout=2)
        ok = (result.error or {}).get("code") == "NETWORK_ERROR"
        self._record("15", ok)
        self.assertTrue(ok)

    def test_16_tls_hostname_mismatch_deny(self) -> None:
        cert_path, key_path = _fixture_cert("other.example")
        httpd = HTTPServer(("127.0.0.1", 0), _TlsMockHandler)
        local_port = httpd.server_address[1]
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        public_ip = "93.184.216.34"
        trust_ctx = ssl.create_default_context()
        trust_ctx.load_verify_locations(cert_path)
        _, connector, _ = _remote_config(
            hostname="sandbox.example.test",
            resolve_fn=lambda _h, _p: (public_ip,),
            ssl_context_factory=lambda: trust_ctx,
        )

        _real_create_connection = socket.create_connection

        def redirect_connection(address, *args, **kwargs):
            host, _ = address
            if host == public_ip:
                address = ("127.0.0.1", local_port)
            return _real_create_connection(address, *args, **kwargs)

        with mock.patch("abis_grp_runtime.connectors.bound_https_transport.socket.create_connection", redirect_connection):
            result = connector.execute("reserve", self._reserve_ctx())
        httpd.shutdown()
        thread.join(timeout=2)
        ok = (result.error or {}).get("code") == "NETWORK_ERROR"
        self._record("16", ok)
        self.assertTrue(ok)

    def test_17_dns_rebinding_no_second_lookup(self) -> None:
        calls = {"n": 0}

        def counting_resolver(host: str, port: int) -> tuple[str, ...]:
            calls["n"] += 1
            return ("93.184.216.34",)

        _, connector, _ = _remote_config(resolve_fn=counting_resolver)
        with mock.patch(
            "abis_grp_runtime.connectors.bound_https_transport.socket.create_connection",
            side_effect=OSError("blocked"),
        ):
            connector.execute("reserve", self._reserve_ctx())
        with mock.patch("socket.getaddrinfo", side_effect=AssertionError("second DNS lookup")):
            with mock.patch(
                "abis_grp_runtime.connectors.bound_https_transport.socket.create_connection",
                side_effect=OSError("blocked"),
            ):
                connector.execute("reserve", self._reserve_ctx())
        ok = calls["n"] >= 2
        self._record("17", ok)
        self.assertGreaterEqual(calls["n"], 2)

    def test_18_missing_credential_remote_deny(self) -> None:
        os.environ.pop("ABIS_TEST_REMOTE_CRED", None)
        cfg, connector, _ = _remote_config()
        result = connector.execute("reserve", self._reserve_ctx())
        ok = (result.error or {}).get("code") == "AUTH_CONFIG_MISSING"
        os.environ["ABIS_TEST_REMOTE_CRED"] = "x"
        self._record("18", ok)
        self.assertTrue(ok)

    def test_19_response_too_large_deny(self) -> None:
        class BigHandler(BaseHTTPRequestHandler):
            def log_message(self, *args: Any) -> None:
                return

            def do_POST(self) -> None:
                body = json.dumps({"blob": "x" * 4096}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        httpd = HTTPServer(("127.0.0.1", 0), BigHandler)
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        cfg = RestaurantHttpAdapterConfig(
            enabled=True,
            adapter_id="local",
            allowlist_id="local",
            target_mode=TargetMode.LOCALHOST_MOCK,
            target_authorization_id="local",
            authorized_hostname="127.0.0.1",
            authorized_port=port,
            base_url=f"http://127.0.0.1:{port}",
            allowed_paths=("/sandbox/v1/reservations",),
            environment_classification=EnvironmentClassification.MOCK,
            timeout_seconds=3.0,
            max_response_bytes=32,
            max_request_body_bytes=16384,
            mapping_version="1",
        )
        result = AuthorizedHttpSandboxConnector(cfg).execute("reserve", self._reserve_ctx())
        httpd.shutdown()
        thread.join(timeout=2)
        code = (result.error or {}).get("code")
        ok = code in {"MALFORMED_EXTERNAL_RESPONSE", "NETWORK_ERROR"}
        self._record("19", ok)
        self.assertIn(code, {"MALFORMED_EXTERNAL_RESPONSE", "NETWORK_ERROR"})

    def test_20_malformed_json_deny(self) -> None:
        class BadJsonHandler(BaseHTTPRequestHandler):
            def log_message(self, *args: Any) -> None:
                return

            def do_POST(self) -> None:
                body = b"not-json"
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        httpd = HTTPServer(("127.0.0.1", 0), BadJsonHandler)
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        cfg = RestaurantHttpAdapterConfig(
            enabled=True,
            adapter_id="local",
            allowlist_id="local",
            target_mode=TargetMode.LOCALHOST_MOCK,
            target_authorization_id="local",
            authorized_hostname="127.0.0.1",
            authorized_port=port,
            base_url=f"http://127.0.0.1:{port}",
            allowed_paths=("/sandbox/v1/reservations",),
            environment_classification=EnvironmentClassification.MOCK,
            timeout_seconds=3.0,
            max_response_bytes=65536,
            max_request_body_bytes=16384,
            mapping_version="1",
        )
        result = AuthorizedHttpSandboxConnector(cfg).execute("reserve", self._reserve_ctx())
        httpd.shutdown()
        thread.join(timeout=2)
        ok = (result.error or {}).get("code") == "MALFORMED_EXTERNAL_RESPONSE"
        self._record("20", ok)
        self.assertTrue(ok)

    def test_21_production_deny(self) -> None:
        ok = not EnvironmentClassification.PRODUCTION.potentially_allowed()
        self._record("21", ok)
        self.assertTrue(ok)

    def test_22_unknown_deny(self) -> None:
        ok = not EnvironmentClassification.UNKNOWN.potentially_allowed()
        self._record("22", ok)
        self.assertTrue(ok)

    def test_23_real_external_deny(self) -> None:
        ok = not resolve_execution_disposition(ExecutionClass.REAL_EXTERNAL).allowed
        self._record("23", ok)
        self.assertTrue(ok)

    def test_24_shopping_not_advertised(self) -> None:
        from abis_grp_runtime.registry.factory import build_reference_registry
        from css.engine import CommerceEngine

        build_reference_registry(ReservationEngine(data_dir=self._tmp.name), CommerceEngine())
        entry = find_advertised_interaction("shopping", "submit_order")
        ok = "AUTHORIZED_NON_PRODUCTION" not in (entry.execution_classes_allowed if entry else [])
        self._record("24", ok)
        self.assertTrue(ok)

    def test_25_external_observe_not_supported(self) -> None:
        from abis_grp_runtime.gateway.reference_profile import build_reference_runtime_profile
        from abis_grp_runtime.registry.factory import build_reference_registry
        from css.engine import CommerceEngine

        build_reference_registry(ReservationEngine(data_dir=self._tmp.name), CommerceEngine())
        profile = build_reference_runtime_profile(GatewayConfig(bearer_token="t"))
        obs = profile.get("technical_observation", {}).get("restaurant", {})
        ok = obs.get("business_outcome_evaluation") == "NOT_IMPLEMENTED"
        self._record("25", ok)
        self.assertTrue(ok)

    def test_26_native_confirmed_not_evaluated(self) -> None:
        httpd = HTTPServer(("127.0.0.1", 0), MockRestaurantHandler)
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        crs = ReservationEngine(data_dir=self._tmp.name)
        adapter = RestaurantBusinessAdapter(
            crs,
            http_adapter_config=RestaurantHttpAdapterConfig(
                enabled=True,
                adapter_id="local",
                allowlist_id="local",
                target_mode=TargetMode.LOCALHOST_MOCK,
                target_authorization_id="local",
                authorized_hostname="127.0.0.1",
                authorized_port=port,
                base_url=f"http://127.0.0.1:{port}",
                allowed_paths=("/sandbox/v1/reservations",),
                environment_classification=EnvironmentClassification.MOCK,
                timeout_seconds=3.0,
                max_response_bytes=65536,
                max_request_body_bytes=16384,
                mapping_version="1",
            ),
        )
        registry = RuntimeInteractionRegistry()
        registry.register(BusinessAdapterRegistration(adapter=adapter, operation="reserve", published=True))
        set_active_registry(registry)
        service = GrokE2EService(registry)
        payload = {
            "agent_id": "a",
            "agent_type": "test",
            "operation": "reserve",
            "execution_class": "AUTHORIZED_NON_PRODUCTION",
            "authorization_token": "ALLOW",
            "correlation_id": "c",
            "vertical": "restaurant",
            "input": self._reserve_ctx(),
        }
        body = service.invoke_from_dict(payload).to_dict()
        httpd.shutdown()
        thread.join(timeout=2)
        ok = (body.get("outcome_disposition") or {}).get("disposition") == "NOT_EVALUATED"
        self._record("26", ok)
        self.assertEqual((body.get("outcome_disposition") or {}).get("disposition"), "NOT_EVALUATED")

    def test_27_credential_absent_from_provenance(self) -> None:
        httpd = HTTPServer(("127.0.0.1", 0), MockRestaurantHandler)
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        cfg = RestaurantHttpAdapterConfig(
            enabled=True,
            adapter_id="local",
            allowlist_id="local",
            target_mode=TargetMode.LOCALHOST_MOCK,
            target_authorization_id="local",
            authorized_hostname="127.0.0.1",
            authorized_port=port,
            base_url=f"http://127.0.0.1:{port}",
            allowed_paths=("/sandbox/v1/reservations",),
            environment_classification=EnvironmentClassification.MOCK,
            timeout_seconds=3.0,
            max_response_bytes=65536,
            max_request_body_bytes=16384,
            mapping_version="1",
            credential_env_var="ABIS_TEST_REMOTE_CRED",
        )
        connector = AuthorizedHttpSandboxConnector(cfg)
        connector.execute("reserve", self._reserve_ctx())
        meta = connector.consume_execution_metadata()
        httpd.shutdown()
        thread.join(timeout=2)
        blob = json.dumps(meta)
        ok = "test-token-secret" not in blob and "Authorization" not in blob
        self._record("27", ok)
        self.assertTrue(ok)

    def test_28_control_metadata_not_in_native_payload(self) -> None:
        httpd = HTTPServer(("127.0.0.1", 0), MockRestaurantHandler)
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        cfg = RestaurantHttpAdapterConfig(
            enabled=True,
            adapter_id="local",
            allowlist_id="local",
            target_mode=TargetMode.LOCALHOST_MOCK,
            target_authorization_id="local",
            authorized_hostname="127.0.0.1",
            authorized_port=port,
            base_url=f"http://127.0.0.1:{port}",
            allowed_paths=("/sandbox/v1/reservations",),
            environment_classification=EnvironmentClassification.MOCK,
            timeout_seconds=3.0,
            max_response_bytes=65536,
            max_request_body_bytes=16384,
            mapping_version="1",
        )
        result = AuthorizedHttpSandboxConnector(cfg).execute("reserve", self._reserve_ctx())
        httpd.shutdown()
        thread.join(timeout=2)
        payload = dict(result.payload or {})
        ok = "egress" not in payload and "target_authorization_id" not in payload
        self._record("28", ok)
        self.assertTrue(ok)

    def test_29_preflight_no_network(self) -> None:
        with mock.patch("socket.getaddrinfo", side_effect=AssertionError("DNS in preflight")):
            body = evaluate_preflight(
                GatewayConfig(bearer_token="t"),
                vertical="restaurant",
                operation="reserve",
                execution_class="AUTHORIZED_NON_PRODUCTION",
            )
        ok = body["preflight_state"] in {"PREFLIGHT_ADAPTER_NOT_CONFIGURED", "PREFLIGHT_READY"}
        self._record("29", ok)
        self.assertIn(body["preflight_state"], {"PREFLIGHT_ADAPTER_NOT_CONFIGURED", "PREFLIGHT_READY"})

    def test_30_no_fallback_to_simulator(self) -> None:
        cfg = RestaurantHttpAdapterConfig(
            enabled=True,
            adapter_id="local",
            allowlist_id="local",
            target_mode=TargetMode.LOCALHOST_MOCK,
            target_authorization_id="local",
            authorized_hostname="127.0.0.1",
            authorized_port=59999,
            base_url="http://127.0.0.1:59999",
            allowed_paths=("/sandbox/v1/reservations",),
            environment_classification=EnvironmentClassification.MOCK,
            timeout_seconds=0.2,
            max_response_bytes=65536,
            max_request_body_bytes=16384,
            mapping_version="1",
        )
        crs = ReservationEngine(data_dir=self._tmp.name)
        adapter = RestaurantBusinessAdapter(crs, http_adapter_config=cfg)
        connector = adapter.get_connector_for_execution_class("AUTHORIZED_NON_PRODUCTION")
        result = connector.execute("reserve", self._reserve_ctx())
        ok = result.technical_status == "TRANSPORT_FAILED"
        self._record("30", ok)
        self.assertEqual(result.technical_status, "TRANSPORT_FAILED")

    def test_31_query_string_path_deny(self) -> None:
        _, _, policy = _remote_config()
        dest, _ = policy.resolve_validated_destination("/sandbox/v1/reservations?x=1")
        self._record("31", dest is None)
        self.assertIsNone(dest)

    def test_32_wildcard_hostname_config_deny(self) -> None:
        cfg = RestaurantHttpAdapterConfig(
            enabled=True,
            adapter_id="x",
            allowlist_id="x",
            target_mode=TargetMode.REMOTE_AUTHORIZED,
            target_authorization_id="x",
            authorized_hostname="*.example.com",
            authorized_port=443,
            base_url="https://sandbox.example.test",
            allowed_paths=("/sandbox/v1/reservations",),
            environment_classification=EnvironmentClassification.SANDBOX,
            timeout_seconds=3.0,
            max_response_bytes=65536,
            max_request_body_bytes=16384,
            mapping_version="1",
            credential_env_var="ABIS_TEST_REMOTE_CRED",
        )
        ok = not cfg.structurally_valid()
        self._record("32", ok)
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
