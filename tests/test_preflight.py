"""Interaction preflight endpoint tests — P2."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.e2e.service import GrokE2EService  # noqa: E402
from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.gateway.preflight import (  # noqa: E402
    PREFLIGHT_EXECUTION_DENIED,
    PREFLIGHT_INVALID_REQUEST,
    PREFLIGHT_NOT_ADVERTISED,
    PREFLIGHT_READY,
)
from abis_grp_runtime.gateway.reference_profile import build_reference_runtime_profile  # noqa: E402
from abis_grp_runtime.gateway.server import start_external_gateway  # noqa: E402
from crs.engine import ReservationEngine  # noqa: E402

TEST_TOKEN = "test-gateway-token-reference-do-not-commit"
URL_PATTERN = re.compile(r"https?://", re.IGNORECASE)


def _ready_payload() -> dict:
    return {"operation": "reserve", "execution_class": "CONTROLLED_SIMULATOR"}


class PreflightTestCase(unittest.TestCase):
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
        self.profile_before = build_reference_runtime_profile(self.config)

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.tmp.cleanup()

    def _post_preflight(self, vertical: str, payload: dict, *, token: str | None = None) -> tuple[int, dict]:
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        req = Request(
            f"{self.base}/v1/demo/{vertical}/preflight",
            data=json.dumps(payload).encode(),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode())
        except HTTPError as exc:
            body = json.loads(exc.read().decode())
            return exc.code, body

    def _get(self, path: str) -> dict:
        with urlopen(f"{self.base}{path}", timeout=5) as resp:
            return json.loads(resp.read().decode())


class TestPreflightStates(PreflightTestCase):
    def test_ready_case(self) -> None:
        status, body = self._post_preflight("restaurant", _ready_payload())
        self.assertEqual(status, 200)
        self.assertEqual(body["preflight_state"], PREFLIGHT_READY)
        self.assertEqual(body["vertical"], "restaurant")
        self.assertEqual(body["operation"], "reserve")
        self.assertEqual(body["execution_class"], "CONTROLLED_SIMULATOR")
        self.assertEqual(body["invocation"]["path"], "/v1/demo/restaurant/invoke")
        self.assertFalse(body["disclaimer"]["business_outcome_prediction"])

    def test_not_advertised_modify(self) -> None:
        status, body = self._post_preflight(
            "restaurant",
            {"operation": "modify", "execution_class": "CONTROLLED_SIMULATOR"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["preflight_state"], PREFLIGHT_NOT_ADVERTISED)
        self.assertNotIn("invocation", body)

    def test_not_advertised_cancel(self) -> None:
        status, body = self._post_preflight(
            "restaurant",
            {"operation": "cancel", "execution_class": "CONTROLLED_SIMULATOR"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["preflight_state"], PREFLIGHT_NOT_ADVERTISED)

    def test_not_advertised_shopping(self) -> None:
        status, body = self._post_preflight("shopping", _ready_payload())
        self.assertEqual(status, 200)
        self.assertEqual(body["preflight_state"], PREFLIGHT_NOT_ADVERTISED)
        self.assertEqual(body["vertical"], "shopping")

    def test_execution_denied_real_external(self) -> None:
        status, body = self._post_preflight(
            "restaurant",
            {"operation": "reserve", "execution_class": "REAL_EXTERNAL"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["preflight_state"], PREFLIGHT_EXECUTION_DENIED)
        self.assertNotIn("invocation", body)

    def test_invalid_missing_operation(self) -> None:
        status, body = self._post_preflight("restaurant", {"execution_class": "CONTROLLED_SIMULATOR"})
        self.assertEqual(status, 200)
        self.assertEqual(body["preflight_state"], PREFLIGHT_INVALID_REQUEST)

    def test_invalid_missing_execution_class(self) -> None:
        status, body = self._post_preflight("restaurant", {"operation": "reserve"})
        self.assertEqual(status, 200)
        self.assertEqual(body["preflight_state"], PREFLIGHT_INVALID_REQUEST)

    def test_malformed_json(self) -> None:
        req = Request(
            f"{self.base}/v1/demo/restaurant/preflight",
            data=b"{not-json",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req, timeout=5)
        body = json.loads(ctx.exception.read().decode())
        self.assertEqual(body["error"]["code"], "REQUEST_INVALID")


class TestPreflightBoundaries(PreflightTestCase):
    def test_no_reservation_business_fields_required(self) -> None:
        status, body = self._post_preflight("restaurant", _ready_payload())
        self.assertEqual(status, 200)
        self.assertEqual(body["preflight_state"], PREFLIGHT_READY)

    def test_no_state_mutation(self) -> None:
        state_path = Path(self.tmp.name) / "state.json"
        before = state_path.read_text(encoding="utf-8") if state_path.exists() else None
        self._post_preflight("restaurant", _ready_payload())
        after = state_path.read_text(encoding="utf-8") if state_path.exists() else None
        self.assertEqual(before, after)

    def test_no_runtime_execution_artifacts(self) -> None:
        _, body = self._post_preflight("restaurant", _ready_payload())
        forbidden = (
            "reservation_id",
            "native_result",
            "outcome_disposition",
            "outcome_evaluation",
            "trace_reference",
            "crs_native_result",
            "transport_status",
        )
        for key in forbidden:
            self.assertNotIn(key, body)

    def test_no_token_exposure(self) -> None:
        _, body = self._post_preflight("restaurant", _ready_payload(), token=TEST_TOKEN)
        serialized = json.dumps(body)
        self.assertNotIn(TEST_TOKEN, serialized)

    def test_relative_invocation_path_only(self) -> None:
        _, body = self._post_preflight("restaurant", _ready_payload())
        path = body["invocation"]["path"]
        self.assertTrue(path.startswith("/"))
        self.assertIsNone(URL_PATTERN.search(path))

    def test_unauthenticated_allowed(self) -> None:
        status, body = self._post_preflight("restaurant", _ready_payload(), token=None)
        self.assertEqual(status, 200)
        self.assertEqual(body["preflight_state"], PREFLIGHT_READY)

    def test_reference_profile_unchanged(self) -> None:
        profile_after = self._get("/v1/reference-profile")
        self.assertEqual(profile_after, self.profile_before)

    def test_health_compatible(self) -> None:
        health = self._get("/health")
        self.assertTrue(health["ok"])
        self.assertEqual(health["operations_allowed"], ["reserve"])


if __name__ == "__main__":
    unittest.main()
