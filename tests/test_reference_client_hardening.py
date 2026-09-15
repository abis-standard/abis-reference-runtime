"""Reference Agent Client hardening — redirect, traversal, malformed response."""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.agent.reference_client import (  # noqa: E402
    ReferenceAgentClient,
    ReferenceClientConfig,
    ReferenceClientError,
)
from abis_grp_runtime.gateway.preflight import PREFLIGHT_READY  # noqa: E402
from abis_grp_runtime.gateway.reference_profile import PROFILE_KIND  # noqa: E402


class TestReferenceClientHardening(unittest.TestCase):
    def _client(self) -> ReferenceAgentClient:
        return ReferenceAgentClient(
            ReferenceClientConfig(
                base_url="http://127.0.0.1:9080",
                vertical="restaurant",
                operation="reserve",
                execution_class="CONTROLLED_SIMULATOR",
                gateway_token="synthetic-token",
            )
        )

    def test_validate_invoke_target_rejects_path_traversal(self) -> None:
        with self.assertRaises(ReferenceClientError):
            ReferenceAgentClient.validate_invoke_target(
                {"method": "POST", "path": "/v1/demo/restaurant/../evil/invoke"}
            )

    def test_validate_invoke_target_rejects_outside_demo_surface(self) -> None:
        with self.assertRaises(ReferenceClientError):
            ReferenceAgentClient.validate_invoke_target(
                {"method": "POST", "path": "/v1/other/restaurant/invoke"}
            )

    def test_validate_invoke_target_rejects_scheme_relative_url(self) -> None:
        with self.assertRaises(ReferenceClientError):
            ReferenceAgentClient.validate_invoke_target({"method": "POST", "path": "//evil.example/invoke"})

    def test_no_redirect_handler_blocks_redirects(self) -> None:
        from abis_grp_runtime.agent import reference_client as rc

        with self.assertRaises(Exception):
            rc._NoRedirectHandler().redirect_request(
                MagicMock(full_url="http://127.0.0.1:9080/v1/reference-profile"),
                None,
                302,
                "Found",
                {},
                "http://evil.example/pivot",
            )

    def test_malformed_invoke_response_fail_closed(self) -> None:
        client = self._client()
        profile = {
            "profile_kind": PROFILE_KIND,
            "profile_version": 1,
            "advertised_interactions": [
                {
                    "vertical": "restaurant",
                    "operation": "reserve",
                    "execution_classes_allowed": ["CONTROLLED_SIMULATOR"],
                    "invocation": {"method": "POST", "path": "/v1/demo/restaurant/invoke"},
                }
            ],
        }
        with patch.object(client, "fetch_profile", return_value=profile):
            with patch.object(
                client,
                "run_preflight",
                return_value={
                    "preflight_state": PREFLIGHT_READY,
                    "invocation": {"method": "POST", "path": "/v1/demo/restaurant/invoke"},
                },
            ):
                with patch.object(client, "invoke", return_value="not-a-dict"):
                    result = client.execute({"correlation_id": "malformed-response"})
        self.assertFalse(result.invoke_attempted)
        self.assertIn("JSON object", result.error or "")

    def test_unexpected_preflight_state_fail_closed(self) -> None:
        client = self._client()
        profile = {
            "profile_kind": PROFILE_KIND,
            "profile_version": 1,
            "advertised_interactions": [
                {
                    "vertical": "restaurant",
                    "operation": "reserve",
                    "execution_classes_allowed": ["CONTROLLED_SIMULATOR"],
                    "invocation": {"method": "POST", "path": "/v1/demo/restaurant/invoke"},
                }
            ],
        }
        with patch.object(client, "fetch_profile", return_value=profile):
            with patch.object(client, "run_preflight", return_value={"preflight_state": "PREFLIGHT_UNKNOWN"}):
                result = client.execute({"correlation_id": "unexpected-preflight"})
        self.assertFalse(result.invoke_attempted)
        self.assertEqual(result.error, "preflight not ready")


if __name__ == "__main__":
    unittest.main()
