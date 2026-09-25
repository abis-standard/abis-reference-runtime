"""D-11B-04 red team patch — F02 mixed DNS and F03 TLS context invariants."""

from __future__ import annotations

import socket
import ssl
import unittest
from unittest import mock

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.connectors.bound_https_transport import (  # noqa: E402
    InsecureTlsContextError,
    default_ssl_context,
    require_secure_tls_context,
    connect_tls,
)
from abis_grp_runtime.connectors.non_production_egress import (  # noqa: E402
    EgressDecision,
    EnvironmentClassification,
    NonProductionEgressPolicy,
    TargetMode,
    ValidatedDestination,
)


class F02MixedDnsFailClosedTestCase(unittest.TestCase):
    def _remote_policy(self, resolve_fn) -> NonProductionEgressPolicy:
        return NonProductionEgressPolicy(
            allowlist_id="test",
            target_mode=TargetMode.REMOTE_AUTHORIZED,
            authorized_hostname="sandbox.example.test",
            authorized_port=443,
            allowed_paths=("/sandbox/v1/reservations",),
            environment_classification=EnvironmentClassification.SANDBOX,
            target_authorization_id="auth-1",
            base_url="https://sandbox.example.test",
            resolve_fn=resolve_fn,
        )

    def _localhost_policy(self, resolve_fn) -> NonProductionEgressPolicy:
        return NonProductionEgressPolicy(
            allowlist_id="test",
            target_mode=TargetMode.LOCALHOST_MOCK,
            authorized_hostname="127.0.0.1",
            authorized_port=8080,
            allowed_paths=("/sandbox/v1/reservations",),
            environment_classification=EnvironmentClassification.MOCK,
            target_authorization_id="auth-local",
            base_url="http://127.0.0.1:8080",
            resolve_fn=resolve_fn,
        )

    def test_public_plus_rfc1918_deny(self) -> None:
        policy = self._remote_policy(lambda _h, _p: ("93.184.216.34", "10.0.0.5"))
        dest, verdict = policy.resolve_validated_destination("/sandbox/v1/reservations")
        self.assertIsNone(dest)
        self.assertEqual(verdict.decision, EgressDecision.DENY)

    def test_public_plus_link_local_deny(self) -> None:
        policy = self._remote_policy(lambda _h, _p: ("93.184.216.34", "169.254.1.1"))
        dest, verdict = policy.resolve_validated_destination("/sandbox/v1/reservations")
        self.assertIsNone(dest)
        self.assertEqual(verdict.decision, EgressDecision.DENY)

    def test_public_plus_loopback_deny(self) -> None:
        policy = self._remote_policy(lambda _h, _p: ("93.184.216.34", "127.0.0.1"))
        dest, _ = policy.resolve_validated_destination("/sandbox/v1/reservations")
        self.assertIsNone(dest)

    def test_public_plus_ipv6_ula_deny(self) -> None:
        policy = self._remote_policy(lambda _h, _p: ("93.184.216.34", "fd12::1"))
        dest, _ = policy.resolve_validated_destination("/sandbox/v1/reservations")
        self.assertIsNone(dest)

    def test_ipv4_mapped_rfc1918_in_mixed_answer_deny(self) -> None:
        policy = self._remote_policy(lambda _h, _p: ("93.184.216.34", "::ffff:10.0.0.5"))
        dest, verdict = policy.resolve_validated_destination("/sandbox/v1/reservations")
        self.assertIsNone(dest)
        self.assertEqual(verdict.decision, EgressDecision.DENY)

    def test_public_only_allow(self) -> None:
        policy = self._remote_policy(lambda _h, _p: ("93.184.216.34",))
        dest, verdict = policy.resolve_validated_destination("/sandbox/v1/reservations")
        self.assertEqual(verdict.decision, EgressDecision.ALLOW)
        self.assertIsNotNone(dest)
        self.assertEqual(dest.selected_ip, "93.184.216.34")

    def test_multi_public_deterministic_selection(self) -> None:
        policy = self._remote_policy(lambda _h, _p: ("198.41.0.4", "93.184.216.34"))
        dest, verdict = policy.resolve_validated_destination("/sandbox/v1/reservations")
        self.assertEqual(verdict.decision, EgressDecision.ALLOW)
        self.assertIsNotNone(dest)
        self.assertEqual(dest.selected_ip, "198.41.0.4")

    def test_localhost_loopback_plus_public_deny(self) -> None:
        policy = self._localhost_policy(lambda _h, _p: ("127.0.0.1", "8.8.8.8"))
        dest, verdict = policy.resolve_validated_destination("/sandbox/v1/reservations")
        self.assertIsNone(dest)
        self.assertEqual(verdict.decision, EgressDecision.DENY)

    def test_localhost_loopback_only_allow(self) -> None:
        policy = self._localhost_policy(lambda _h, _p: ("127.0.0.1", "::1"))
        dest, verdict = policy.resolve_validated_destination("/sandbox/v1/reservations")
        self.assertEqual(verdict.decision, EgressDecision.ALLOW)
        self.assertIsNotNone(dest)
        self.assertEqual(dest.selected_ip, "127.0.0.1")


class F03TlsContextInvariantTestCase(unittest.TestCase):
    def _destination(self) -> ValidatedDestination:
        return ValidatedDestination(
            target_mode=TargetMode.REMOTE_AUTHORIZED,
            authorized_hostname="sandbox.example.test",
            authorized_port=443,
            resolved_ips=("93.184.216.34",),
            selected_ip="93.184.216.34",
            request_path="/sandbox/v1/reservations",
            scheme="https",
        )

    def test_default_ssl_context_secure(self) -> None:
        ctx = default_ssl_context()
        require_secure_tls_context(ctx)
        self.assertTrue(ctx.check_hostname)
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)

    def test_check_hostname_false_denied(self) -> None:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with self.assertRaises(InsecureTlsContextError):
            require_secure_tls_context(ctx)

    def test_cert_required_not_set_denied(self) -> None:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with self.assertRaises(InsecureTlsContextError):
            require_secure_tls_context(ctx)

    def test_secure_custom_context_usable(self) -> None:
        ctx = ssl.create_default_context()
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        require_secure_tls_context(ctx)

    def test_connect_tls_rejects_insecure_before_tcp(self) -> None:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with mock.patch("abis_grp_runtime.connectors.bound_https_transport.socket.create_connection") as create:
            with self.assertRaises(InsecureTlsContextError):
                connect_tls(self._destination(), timeout=1.0, ssl_context=ctx)
            create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
