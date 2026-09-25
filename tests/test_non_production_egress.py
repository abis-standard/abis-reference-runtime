"""Non-production egress policy tests."""

from __future__ import annotations

import unittest

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.connectors.non_production_egress import (  # noqa: E402
    EnvironmentClassification,
    EgressDecision,
    NonProductionEgressPolicy,
    TargetMode,
)


class NonProductionEgressPolicyTestCase(unittest.TestCase):
    def _policy(self, **kwargs: object) -> NonProductionEgressPolicy:
        defaults = {
            "allowlist_id": "test-allowlist",
            "target_mode": TargetMode.LOCALHOST_MOCK,
            "authorized_hostname": "127.0.0.1",
            "authorized_port": 9095,
            "base_url": "http://127.0.0.1:9095",
            "allowed_paths": ("/sandbox/v1/reservations",),
            "environment_classification": EnvironmentClassification.MOCK,
            "target_authorization_id": "test-authz",
        }
        defaults.update(kwargs)
        return NonProductionEgressPolicy(**defaults)  # type: ignore[arg-type]

    def test_production_environment_denied(self) -> None:
        policy = self._policy(environment_classification=EnvironmentClassification.PRODUCTION)
        verdict = policy.evaluate_environment()
        self.assertEqual(verdict.decision, EgressDecision.DENY)

    def test_unknown_environment_denied(self) -> None:
        policy = self._policy(environment_classification=EnvironmentClassification.UNKNOWN)
        self.assertEqual(policy.evaluate_environment().decision, EgressDecision.DENY)

    def test_localhost_allowlisted_path_permitted(self) -> None:
        policy = self._policy()
        url, verdict = policy.resolve_request_url("/sandbox/v1/reservations")
        self.assertEqual(verdict.decision, EgressDecision.ALLOW)
        self.assertIsNotNone(url)
        self.assertIn("/sandbox/v1/reservations", url or "")

    def test_non_allowlisted_path_denied(self) -> None:
        policy = self._policy()
        url, verdict = policy.resolve_request_url("/other/path")
        self.assertIsNone(url)
        self.assertEqual(verdict.decision, EgressDecision.DENY)

    def test_remote_https_hostname_permitted_with_resolver(self) -> None:
        def resolver(host: str, port: int) -> tuple[str, ...]:
            self.assertEqual(host, "sandbox.example.test")
            return ("93.184.216.34",)

        policy = self._policy(
            target_mode=TargetMode.REMOTE_AUTHORIZED,
            authorized_hostname="sandbox.example.test",
            authorized_port=443,
            base_url="https://sandbox.example.test",
            resolve_fn=resolver,
        )
        dest, verdict = policy.resolve_validated_destination("/sandbox/v1/reservations")
        self.assertEqual(verdict.decision, EgressDecision.ALLOW)
        self.assertIsNotNone(dest)
        self.assertEqual(dest.selected_ip, "93.184.216.34")

    def test_rfc1918_resolved_denied_for_remote(self) -> None:
        policy = self._policy(
            target_mode=TargetMode.REMOTE_AUTHORIZED,
            authorized_hostname="sandbox.example.test",
            authorized_port=443,
            base_url="https://sandbox.example.test",
            resolve_fn=lambda _h, _p: ("192.168.1.10",),
        )
        dest, verdict = policy.resolve_validated_destination("/sandbox/v1/reservations")
        self.assertIsNone(dest)
        self.assertEqual(verdict.decision, EgressDecision.DENY)


if __name__ == "__main__":
    unittest.main()
