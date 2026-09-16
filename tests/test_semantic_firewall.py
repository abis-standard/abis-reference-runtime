"""Semantic firewall — prohibited affirmative claims in public Runtime output."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from urllib.request import Request, urlopen

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.gateway.server import start_external_gateway  # noqa: E402
from tests._service import make_test_service  # noqa: E402

TEST_TOKEN = "test-gateway-token-reference-do-not-commit"

FORBIDDEN_AFFIRMATIVE_PATTERNS = [
    r"ABIS Capability Manifest",
    r"Capability Manifest",
    r"ABIS Compatible",
    r"ABIS Conformant",
    r"ABIS Certified",
    r"ABIS Discovery Standard",
    r"ABIS Business Manifest",
    r"ABIS Conformance Manifest",
    r"ABIS Compatibility Manifest",
    r"/\.well-known/abis(?!-reference-runtime)",
    r"Interaction Readiness Catalog",
    r"readiness catalog",
    r'"provider_hint"\s*:\s*"',
    r"payment authorized",
    r"payment success",
    r"Business Outcome SUCCESS",
    r"Business Outcome FAILURE",
    r"conformance level",
    r"certification status",
    r'"trust_level"\s*:\s*"',
]


class SemanticFirewallTestCase(unittest.TestCase):
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

    def _collect_public_outputs(self) -> list[str]:
        paths = [
            "/v1/reference-profile",
            "/v1/reference-profile/interactions/restaurant/reserve",
            "/v1/reference-profile/interactions/shopping/submit_order",
            "/health",
        ]
        bodies: list[str] = []
        for path in paths:
            with urlopen(f"{self.base}{path}", timeout=5) as resp:
                bodies.append(resp.read().decode())
        preflight_req = Request(
            f"{self.base}/v1/demo/restaurant/preflight",
            data=json.dumps({"operation": "reserve", "execution_class": "CONTROLLED_SIMULATOR"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(preflight_req, timeout=5) as resp:
            bodies.append(resp.read().decode())
        return bodies

    def test_no_prohibited_affirmative_claims(self) -> None:
        for body in self._collect_public_outputs():
            for pattern in FORBIDDEN_AFFIRMATIVE_PATTERNS:
                self.assertIsNone(
                    re.search(pattern, body, re.IGNORECASE),
                    msg=f"forbidden pattern {pattern} in {body[:200]}",
                )


if __name__ == "__main__":
    unittest.main()
