"""Cross-vertical Profile and Descriptor surface tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from urllib.request import Request, urlopen

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.gateway.server import start_external_gateway  # noqa: E402
from tests._service import make_test_service  # noqa: E402

TEST_TOKEN = "test-gateway-token-reference-do-not-commit"


class CrossVerticalSurfaceTestCase(unittest.TestCase):
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

    def _get(self, path: str) -> dict:
        with urlopen(f"{self.base}{path}", timeout=5) as resp:
            return json.loads(resp.read().decode())

    def test_profile_lists_both_verticals(self) -> None:
        profile = self._get("/v1/reference-profile")
        interactions = profile["advertised_interactions"]
        paths = {(i["vertical"], i["operation"], i["descriptor_path"]) for i in interactions}
        self.assertIn(
            ("restaurant", "reserve", "/v1/reference-profile/interactions/restaurant/reserve"),
            paths,
        )
        self.assertIn(
            ("shopping", "submit_order", "/v1/reference-profile/interactions/shopping/submit_order"),
            paths,
        )

    def test_descriptor_paths_match_profile(self) -> None:
        profile = self._get("/v1/reference-profile")
        for item in profile["advertised_interactions"]:
            descriptor = self._get(item["descriptor_path"])
            self.assertEqual(descriptor["vertical"], item["vertical"])
            self.assertEqual(descriptor["operation"], item["operation"])


if __name__ == "__main__":
    unittest.main()
