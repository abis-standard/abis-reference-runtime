"""Non-production egress policy tests."""

from __future__ import annotations

import unittest

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.connectors.non_production_egress import (  # noqa: E402
    EnvironmentClassification,
    EgressDecision,
    NonProductionEgressPolicy,
)


class NonProductionEgressPolicyTestCase(unittest.TestCase):
    def _policy(self, **kwargs: object) -> NonProductionEgressPolicy:
        defaults = {
            "allowlist_id": "test-allowlist",
            "base_url": "http://127.0.0.1:9095",
            "allowed_paths": ("/sandbox/v1/reservations",),
            "environment_classification": EnvironmentClassification.MOCK,
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

    def test_remote_https_hostname_denied(self) -> None:
        policy = self._policy(
            base_url="https://sandbox.company.example",
            allowed_paths=("/sandbox/v1/reservations",),
        )
        url, verdict = policy.resolve_request_url("/sandbox/v1/reservations")
        self.assertIsNone(url)
        self.assertEqual(verdict.decision, EgressDecision.DENY)

    def test_rfc1918_base_denied(self) -> None:
        policy = self._policy(base_url="http://192.168.1.10:8080")
        url, verdict = policy.resolve_request_url("/sandbox/v1/reservations")
        self.assertIsNone(url)
        self.assertEqual(verdict.decision, EgressDecision.DENY)


if __name__ == "__main__":
    unittest.main()
