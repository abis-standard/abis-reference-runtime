"""Interaction Descriptor endpoint and contract tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.descriptor.constants import DESCRIPTOR_KIND, DESCRIPTOR_VERSION  # noqa: E402
from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.gateway.server import start_external_gateway  # noqa: E402
from tests._service import make_test_service  # noqa: E402

TEST_TOKEN = "test-gateway-token-reference-do-not-commit"


class DescriptorTestCase(unittest.TestCase):
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

    def _get(self, path: str) -> tuple[int, dict]:
        req = Request(f"{self.base}{path}", method="GET")
        try:
            with urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode())
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode())


class TestDescriptorEndpoint(DescriptorTestCase):
    def test_restaurant_descriptor_200(self) -> None:
        status, body = self._get("/v1/reference-profile/interactions/restaurant/reserve")
        self.assertEqual(status, 200)
        self.assertEqual(body["descriptor_kind"], DESCRIPTOR_KIND)
        self.assertEqual(body["descriptor_version"], DESCRIPTOR_VERSION)
        self.assertEqual(body["authority"]["semantic"], "NONE")
        self.assertEqual(body["authority"]["normative"], "NONE")
        self.assertIn("structured_input", body)
        self.assertIn("preflight", body)
        self.assertIn("invocation", body)
        self.assertTrue(body["disclaimer"]["implementation_metadata_only"])

    def test_shopping_descriptor_200(self) -> None:
        status, body = self._get("/v1/reference-profile/interactions/shopping/submit_order")
        self.assertEqual(status, 200)
        self.assertEqual(body["vertical"], "shopping")
        self.assertEqual(body["operation"], "submit_order")

    def test_unknown_interaction_404(self) -> None:
        status, _ = self._get("/v1/reference-profile/interactions/travel/book")
        self.assertEqual(status, 404)

    def test_unpublished_operation_404(self) -> None:
        status, _ = self._get("/v1/reference-profile/interactions/restaurant/modify")
        self.assertEqual(status, 404)

    def test_no_auth_required(self) -> None:
        status, _ = self._get("/v1/reference-profile/interactions/restaurant/reserve")
        self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()
