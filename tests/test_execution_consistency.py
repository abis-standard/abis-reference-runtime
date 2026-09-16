"""Execution surface consistency — Profile = Preflight = Invoke gateway truth."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.gateway.execution_surface import (  # noqa: E402
    advertised_interactions,
    find_advertised_interaction,
    is_advertised_invocation,
    reference_execution_surface,
)
from abis_grp_runtime.gateway.preflight import (  # noqa: E402
    PREFLIGHT_EXECUTION_DENIED,
    PREFLIGHT_NOT_ADVERTISED,
    PREFLIGHT_READY,
    evaluate_preflight,
)
from abis_grp_runtime.gateway.reference_profile import build_reference_runtime_profile  # noqa: E402
from abis_grp_runtime.gateway.server import start_external_gateway  # noqa: E402
from tests._service import make_test_service  # noqa: E402

TEST_TOKEN = "test-gateway-token-reference-do-not-commit"


def _invoke_payload(
    *,
    vertical: str = "restaurant",
    operation: str = "reserve",
    execution_class: str = "CONTROLLED_SIMULATOR",
    correlation_id: str,
) -> dict:
    if vertical == "shopping" and operation == "submit_order":
        structured = {
            "sku_id": "SKU-DEMO-001",
            "quantity": 1,
            "idempotency_key": f"idem-{correlation_id}",
            "test_scenario": "NORMAL_SUCCESS",
        }
    else:
        structured = {
            "date": "2026-09-12",
            "time": "20:00",
            "party_size": 4,
            "seating_type": "PRIVATE_ROOM",
            "customer_reference": "TEST-CUST-CONSISTENCY",
            "idempotency_key": f"idem-{correlation_id}",
            "test_scenario": "NORMAL_SUCCESS",
        }
    return {
        "agent_id": "consistency-agent-001",
        "agent_type": "reference-agent",
        "operation": operation,
        "execution_class": execution_class,
        "authorization_token": "ALLOW",
        "correlation_id": correlation_id,
        "input": structured,
    }


CONSISTENCY_MATRIX = [
    {
        "vertical": "restaurant",
        "operation": "reserve",
        "execution_class": "CONTROLLED_SIMULATOR",
        "advertised": True,
        "preflight_state": PREFLIGHT_READY,
        "invoke_permitted": True,
    },
    {
        "vertical": "restaurant",
        "operation": "modify",
        "execution_class": "CONTROLLED_SIMULATOR",
        "advertised": False,
        "preflight_state": PREFLIGHT_NOT_ADVERTISED,
        "invoke_permitted": False,
    },
    {
        "vertical": "restaurant",
        "operation": "cancel",
        "execution_class": "CONTROLLED_SIMULATOR",
        "advertised": False,
        "preflight_state": PREFLIGHT_NOT_ADVERTISED,
        "invoke_permitted": False,
    },
    {
        "vertical": "shopping",
        "operation": "reserve",
        "execution_class": "CONTROLLED_SIMULATOR",
        "advertised": False,
        "preflight_state": PREFLIGHT_NOT_ADVERTISED,
        "invoke_permitted": False,
    },
    {
        "vertical": "shopping",
        "operation": "submit_order",
        "execution_class": "CONTROLLED_SIMULATOR",
        "advertised": True,
        "preflight_state": PREFLIGHT_READY,
        "invoke_permitted": True,
    },
    {
        "vertical": "restaurant",
        "operation": "reserve",
        "execution_class": "REAL_EXTERNAL",
        "advertised": False,
        "preflight_state": PREFLIGHT_EXECUTION_DENIED,
        "invoke_permitted": False,
    },
]


class ExecutionConsistencyTestCase(unittest.TestCase):
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

    def _reservation_count(self) -> int:
        state_path = Path(self.tmp.name) / "state.json"
        if not state_path.is_file():
            return 0
        state = json.loads(state_path.read_text(encoding="utf-8"))
        return len(state.get("reservations") or {})

    def _post_preflight(self, vertical: str, operation: str, execution_class: str) -> dict:
        req = Request(
            f"{self.base}/v1/demo/{vertical}/preflight",
            data=json.dumps({"operation": operation, "execution_class": execution_class}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())

    def _post_invoke(self, vertical: str, payload: dict) -> tuple[int, dict]:
        req = Request(
            f"{self.base}/v1/demo/{vertical}/invoke",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {TEST_TOKEN}",
            },
            method="POST",
        )
        try:
            with urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode())
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode())

    def test_execution_surface_is_single_source_for_profile(self) -> None:
        profile = build_reference_runtime_profile(self.config)
        self.assertEqual(profile["advertised_interactions"], advertised_interactions())

    def test_every_advertised_interaction_is_preflight_ready_and_invokable(self) -> None:
        for item in reference_execution_surface():
            preflight = evaluate_preflight(
                self.config,
                vertical=item.vertical,
                operation=item.operation,
                execution_class=sorted(item.execution_classes_allowed)[0],
            )
            self.assertEqual(preflight["preflight_state"], PREFLIGHT_READY)
            status, body = self._post_invoke(
                item.vertical,
                _invoke_payload(
                    vertical=item.vertical,
                    operation=item.operation,
                    execution_class=sorted(item.execution_classes_allowed)[0],
                    correlation_id=f"surface-{item.vertical}-{item.operation}",
                ),
            )
            self.assertEqual(status, 200, body)
            self.assertEqual(body["transport_status"], "ACCEPTED")

    def test_consistency_matrix(self) -> None:
        profile = build_reference_runtime_profile(self.config)
        advertised = profile["advertised_interactions"]
        before_count = self._reservation_count()

        for case in CONSISTENCY_MATRIX:
            with self.subTest(**case):
                vertical = case["vertical"]
                operation = case["operation"]
                execution_class = case["execution_class"]

                profile_match = find_advertised_interaction(vertical, operation)
                profile_advertises = profile_match is not None and execution_class in profile_match.execution_classes_allowed
                self.assertEqual(
                    bool(profile_advertises),
                    case["advertised"],
                    msg="profile advertisement mismatch",
                )
                self.assertEqual(
                    is_advertised_invocation(vertical, operation, execution_class),
                    case["advertised"],
                )

                preflight = self._post_preflight(vertical, operation, execution_class)
                self.assertEqual(preflight["preflight_state"], case["preflight_state"])

                status, body = self._post_invoke(
                    vertical,
                    _invoke_payload(
                        vertical=vertical,
                        operation=operation,
                        execution_class=execution_class,
                        correlation_id=f"matrix-{vertical}-{operation}-{execution_class}",
                    ),
                )
                if case["invoke_permitted"]:
                    self.assertEqual(status, 200, body)
                    self.assertEqual(body["transport_status"], "ACCEPTED")
                else:
                    self.assertIn(status, (403, 404), body)
                    self.assertIn("error", body)

        if before_count == 0:
            permitted = sum(1 for c in CONSISTENCY_MATRIX if c["invoke_permitted"] and c["vertical"] == "restaurant")
            self.assertEqual(self._reservation_count(), permitted)


if __name__ == "__main__":
    unittest.main()
