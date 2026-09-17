"""v0.6 semantic firewall — negative inference guards."""

from __future__ import annotations

import json
import tempfile
import unittest
import uuid
from urllib.request import Request, urlopen

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.gateway.server import start_external_gateway  # noqa: E402
from tests._service import make_test_service  # noqa: E402

TEST_TOKEN = "test-v06-firewall-token-do-not-commit"


class V06SemanticFirewallTestCase(unittest.TestCase):
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

    def _post(self, path: str, payload: dict) -> dict:
        req = Request(
            f"{self.base}{path}",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {TEST_TOKEN}",
            },
            method="POST",
        )
        with urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())

    def test_no_composite_business_outcome_fields(self) -> None:
        profile = json.loads(
            urlopen(f"{self.base}/v1/reference-profile", timeout=5).read().decode()
        )
        forbidden_affirmative = (
            "trip_business_outcome",
            "composite_outcome",
            "outcome_equivalence_engine",
            "business_outcome_success",
            "business_outcome_failure",
            "determine_business_outcome",
            "evaluate_outcome",
        )
        blob = json.dumps(profile).lower()
        for token in forbidden_affirmative:
            self.assertNotIn(token, blob)
        self.assertEqual(
            profile["outcome_boundary"]["normative_business_outcome_evaluation"],
            "NOT_IMPLEMENTED",
        )
        self.assertEqual(profile["outcome_boundary"]["completion_determination"], "NOT_IMPLEMENTED")

    def test_multiple_native_results_do_not_aggregate_outcome(self) -> None:
        """Flight/Hotel/Restaurant style multi-object — no Trip Business Outcome."""
        icr = str(uuid.uuid4())
        results = []
        for idx, scenario in enumerate(("NORMAL_SUCCESS", "PENDING", "NORMAL_SUCCESS")):
            body = self._post(
                "/v1/demo/restaurant/invoke",
                {
                    "agent_id": "multi-obj-agent",
                    "agent_type": "reference-agent",
                    "operation": "reserve",
                    "execution_class": "CONTROLLED_SIMULATOR",
                    "authorization_token": "ALLOW",
                    "correlation_id": f"multi-obj-{idx}",
                    "implementation_continuity_reference": icr,
                    "input": {
                        "date": "2026-09-12",
                        "time": "20:00",
                        "party_size": 2,
                        "seating_type": "PRIVATE_ROOM",
                        "customer_reference": f"CUST-{idx}",
                        "idempotency_key": f"idem-multi-{idx}",
                        "test_scenario": scenario,
                    },
                },
            )
            results.append(body)

        self.assertEqual(len({r["native_result"]["external_identifier"] for r in results}), 3)
        for body in results:
            self.assertEqual(body["outcome_disposition"]["disposition"], "NOT_EVALUATED")
            self.assertNotIn("trip_outcome", body)
            self.assertNotIn("composite_outcome", body)

        observe_body = self._post(
            "/v1/demo/restaurant/observe",
            {
                "correlation_id": "multi-observe",
                "external_identifier": results[1]["native_result"]["external_identifier"],
                "implementation_continuity_reference": icr,
            },
        )
        self.assertEqual(observe_body["outcome_disposition"]["disposition"], "NOT_EVALUATED")
        self.assertNotIn("composite_outcome", observe_body)
