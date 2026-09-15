"""Reference Runtime Profile endpoint tests — P1."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from urllib.request import Request, urlopen

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.version import __version__  # noqa: E402
from abis_grp_runtime.e2e.service import GrokE2EService  # noqa: E402
from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.gateway.reference_profile import (  # noqa: E402
    PROFILE_KIND,
    PROFILE_VERSION,
    build_reference_runtime_profile,
)
from abis_grp_runtime.gateway.server import start_external_gateway  # noqa: E402
from crs.engine import ReservationEngine  # noqa: E402

TEST_TOKEN = "test-gateway-token-reference-do-not-commit"
FORBIDDEN_SEMANTIC_TERMS = (
    "Capability Manifest",
    "ABIS Capability Manifest",
    "ABIS Compatible",
    "ABIS Conformant",
    "ABIS Certified",
    "/.well-known/abis",
)
FORBIDDEN_OUTCOME_TERMS = ("MATCH", "MISMATCH", "PARTIAL", "SUCCESS", "FAILURE")
URL_PATTERN = re.compile(r"https?://", re.IGNORECASE)


class ReferenceProfileTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = ReservationEngine(data_dir=self.tmp.name)
        self.service = GrokE2EService(self.engine)
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

    def _get(self, path: str) -> tuple[int, dict[str, object], str]:
        req = Request(f"{self.base}{path}", method="GET")
        with urlopen(req, timeout=5) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw), resp.headers.get("Content-Type", "")


class TestReferenceProfileEndpoint(ReferenceProfileTestCase):
    def test_reference_profile_returns_200_json(self) -> None:
        status, body, content_type = self._get("/v1/reference-profile")
        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)

    def test_required_profile_fields(self) -> None:
        _, body, _ = self._get("/v1/reference-profile")
        self.assertEqual(body["profile_kind"], PROFILE_KIND)
        self.assertEqual(body["profile_version"], PROFILE_VERSION)
        self.assertEqual(body["runtime"]["version"], __version__)
        self.assertEqual(body["authority"]["semantic"], "NONE")
        self.assertEqual(body["authority"]["normative"], "NONE")

    def test_advertised_interactions_match_gateway_truth(self) -> None:
        _, body, _ = self._get("/v1/reference-profile")
        interactions = body["advertised_interactions"]
        self.assertEqual(len(interactions), 1)
        item = interactions[0]
        self.assertEqual(item["vertical"], "restaurant")
        self.assertEqual(item["operation"], "reserve")
        self.assertEqual(item["execution_classes_allowed"], ["CONTROLLED_SIMULATOR"])
        self.assertEqual(item["invocation"]["method"], "POST")
        self.assertEqual(item["invocation"]["path"], "/v1/demo/restaurant/invoke")
        self.assertNotIn("check_availability", json.dumps(interactions))
        self.assertNotIn("modify", json.dumps(interactions))
        self.assertNotIn("cancel", json.dumps(interactions))

    def test_execution_and_outcome_boundaries(self) -> None:
        _, body, _ = self._get("/v1/reference-profile")
        self.assertEqual(body["execution_boundary"]["real_execution"], "PROHIBITED")
        self.assertEqual(
            body["outcome_boundary"]["normative_business_outcome_evaluation"],
            "NOT_IMPLEMENTED",
        )
        self.assertNotIn("REAL_EXTERNAL", json.dumps(body["advertised_interactions"]))

    def test_authorization_disclosure_without_secrets(self) -> None:
        _, body, _ = self._get("/v1/reference-profile")
        invoke_auth = body["authorization"]["invoke"]
        self.assertTrue(invoke_auth["required"])
        self.assertEqual(invoke_auth["scheme"], "bearer")
        serialized = json.dumps(body)
        self.assertNotIn(TEST_TOKEN, serialized)
        self.assertNotIn("ABIS_DEMO_GATEWAY_TOKEN", serialized)

    def test_relative_invocation_paths_only(self) -> None:
        _, body, _ = self._get("/v1/reference-profile")
        for item in body["advertised_interactions"]:
            path = item["invocation"]["path"]
            self.assertTrue(path.startswith("/"))
            self.assertIsNone(URL_PATTERN.search(path))

    def test_semantic_firewall_absence(self) -> None:
        _, body, _ = self._get("/v1/reference-profile")
        serialized = json.dumps(body)
        for term in FORBIDDEN_SEMANTIC_TERMS:
            self.assertNotIn(term, serialized, msg=f"forbidden term present: {term}")
        self.assertNotIn('"outcome_evaluation"', serialized)
        for term in FORBIDDEN_OUTCOME_TERMS:
            self.assertNotIn(term, serialized, msg=f"forbidden outcome term present: {term}")

    def test_profile_builder_matches_endpoint(self) -> None:
        expected = build_reference_runtime_profile(self.config)
        _, body, _ = self._get("/v1/reference-profile")
        self.assertEqual(body, expected)


class TestHealthCompatibility(ReferenceProfileTestCase):
    def test_health_remains_available(self) -> None:
        status, body, _ = self._get("/health")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["verticals_enabled"], ["restaurant"])
        self.assertEqual(body["operations_allowed"], ["reserve"])
        self.assertEqual(body["execution_class_allowed"], ["CONTROLLED_SIMULATOR"])
        self.assertEqual(body["real_execution"], "PROHIBITED")
        self.assertEqual(body["semantic_authority"], "NONE")
        self.assertEqual(body["reference_runtime"], f"v{__version__}")


if __name__ == "__main__":
    unittest.main()
