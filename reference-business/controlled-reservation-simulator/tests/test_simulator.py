"""unittest suite for Controlled Reservation Simulator (M-203).

Covers engine, inventory, idempotency, scenarios (incl. Golden), HTTP API,
persistence lifecycle, and asserts no ABIS outcome keys in any response.
"""

from __future__ import annotations

import json
import threading
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from crs.api import handle_request
from crs.engine import ReservationEngine
from crs.inventory import TEMPLATE_SLOTS, query_availability, slots_for_date
from crs.models import (
    FORBIDDEN_ABIS_KEYS,
    SEATING_PRIVATE_ROOM,
    SEATING_TABLE,
    STATUS_CANCELLED,
    STATUS_CONFIRMED,
    STATUS_PENDING,
    STATUS_REJECTED,
    assert_no_abis_keys,
)
from crs.scenarios import ALL_SCENARIOS
from crs.server import make_handler


def _assert_native_envelope(tc: unittest.TestCase, result: dict) -> None:
    for key in (
        "business_system",
        "operation",
        "status",
        "transport_ok",
        "timestamp",
        "classification",
        "semantic_authority",
    ):
        tc.assertIn(key, result)
    tc.assertEqual(result["business_system"], "abis-demo-restaurant-simulator")
    tc.assertEqual(result["classification"], "EXTERNAL_BUSINESS_SYSTEM_TEST_DOUBLE")
    tc.assertEqual(result["semantic_authority"], "NONE")
    found = assert_no_abis_keys(result)
    tc.assertEqual(found, [], f"Forbidden ABIS keys present: {found}")
    for bad in FORBIDDEN_ABIS_KEYS:
        tc.assertNotIn(bad, result)


class TestInventory(unittest.TestCase):
    """Req: deterministic inventory for 2026-09-12; any date clones template."""

    def test_template_slots_2026_09_12(self):
        slots = { (s["time"], s["seating_type"]): s for s in slots_for_date("2026-09-12") }
        pr = SEATING_PRIVATE_ROOM
        self.assertEqual(slots[("18:00", pr)]["capacity"], 4)
        self.assertEqual(slots[("18:00", pr)]["availability"], "AVAILABLE")
        self.assertEqual(slots[("18:30", pr)]["capacity"], 2)
        self.assertEqual(slots[("18:30", pr)]["availability"], "UNAVAILABLE")
        self.assertEqual(slots[("19:00", pr)]["capacity"], 4)
        self.assertEqual(slots[("19:00", pr)]["availability"], "UNAVAILABLE")
        self.assertEqual(slots[("19:30", pr)]["capacity"], 0)
        self.assertEqual(slots[("19:30", pr)]["availability"], "UNAVAILABLE")
        self.assertEqual(slots[("20:00", pr)]["capacity"], 8)
        self.assertEqual(slots[("20:00", pr)]["availability"], "AVAILABLE")

    def test_any_date_clones_template(self):
        a = [(s["time"], s["capacity"], s["availability"], s["seating_type"]) for s in slots_for_date("2026-09-12")]
        b = [(s["time"], s["capacity"], s["availability"], s["seating_type"]) for s in slots_for_date("2099-01-01")]
        self.assertEqual(a, b)

    def test_query_filters(self):
        avail = query_availability("2026-09-12", party_size=4, seating_type=SEATING_PRIVATE_ROOM)
        times = [s["time"] for s in avail]
        self.assertIn("18:00", times)
        self.assertIn("20:00", times)
        self.assertNotIn("19:00", times)


class TestEngineLifecycle(unittest.TestCase):
    """Req: reserve→lookup→modify→lookup→cancel→lookup persistence."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = ReservationEngine(data_dir=self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_full_lifecycle(self):
        r = self.engine.reserve(
            date="2026-09-12",
            time="18:00",
            party_size=2,
            seating_type=SEATING_PRIVATE_ROOM,
            customer_reference="TEST-CUST-AAA",
            idempotency_key="idem-life-1",
        )
        _assert_native_envelope(self, r)
        self.assertEqual(r["status"], STATUS_CONFIRMED)
        self.assertTrue(r["transport_ok"])
        rid = r["reservation_id"]
        self.assertTrue(rid.startswith("TEST-RSV-"))

        g1 = self.engine.get(rid)
        _assert_native_envelope(self, g1)
        self.assertEqual(g1["actual"]["time"], "18:00")

        m = self.engine.modify(rid, {"party_size": 3})
        _assert_native_envelope(self, m)
        self.assertEqual(m["actual"]["party_size"], 3)

        g2 = self.engine.get(rid)
        self.assertEqual(g2["actual"]["party_size"], 3)

        c = self.engine.cancel(rid)
        _assert_native_envelope(self, c)
        self.assertEqual(c["status"], STATUS_CANCELLED)

        g3 = self.engine.get(rid)
        self.assertEqual(g3["status"], STATUS_CANCELLED)

        # Persisted on disk
        state = json.loads((Path(self.tmp.name) / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["reservations"][rid]["status"], STATUS_CANCELLED)

    def test_identity_constants(self):
        r = self.engine.availability("2026-09-12", party_size=2)
        self.assertEqual(r["business_system"], "abis-demo-restaurant-simulator")
        self.assertEqual(r.get("restaurant"), "ABIS Demo Restaurant")


class TestIdempotency(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = ReservationEngine(data_dir=self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_same_key_same_request_replays(self):
        kwargs = dict(
            date="2026-09-12",
            time="20:00",
            party_size=4,
            seating_type=SEATING_PRIVATE_ROOM,
            customer_reference="TEST-CUST-IDEM",
            idempotency_key="idem-same",
        )
        r1 = self.engine.reserve(**kwargs)
        r2 = self.engine.reserve(**kwargs)
        self.assertEqual(r1["reservation_id"], r2["reservation_id"])
        self.assertTrue(r2.get("idempotent_replay"))
        _assert_native_envelope(self, r2)

    def test_same_key_conflicting_request(self):
        self.engine.reserve(
            date="2026-09-12",
            time="20:00",
            party_size=4,
            seating_type=SEATING_PRIVATE_ROOM,
            customer_reference="TEST-CUST-A",
            idempotency_key="idem-conflict",
        )
        r2 = self.engine.reserve(
            date="2026-09-12",
            time="18:00",
            party_size=2,
            seating_type=SEATING_PRIVATE_ROOM,
            customer_reference="TEST-CUST-B",
            idempotency_key="idem-conflict",
        )
        self.assertEqual(r2.get("error"), "IDEMPOTENCY_CONFLICT")
        self.assertEqual(r2["status"], STATUS_REJECTED)
        # Native conflict — not ABIS verdict
        _assert_native_envelope(self, r2)


class TestScenarios(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = ReservationEngine(data_dir=self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _reserve(self, scenario, **overrides):
        kwargs = dict(
            date="2026-09-12",
            time="18:00",
            party_size=4,
            seating_type=SEATING_PRIVATE_ROOM,
            customer_reference="TEST-CUST-SCN",
            idempotency_key=f"idem-{scenario}",
            test_scenario=scenario,
        )
        kwargs.update(overrides)
        return self.engine.reserve(**kwargs)

    def test_all_scenario_names_defined(self):
        self.assertEqual(len(ALL_SCENARIOS), 12)

    def test_normal_success(self):
        r = self._reserve("NORMAL_SUCCESS", idempotency_key="idem-ns")
        self.assertEqual(r["status"], STATUS_CONFIRMED)
        self.assertTrue(r["transport_ok"])
        _assert_native_envelope(self, r)

    def test_no_availability(self):
        r = self._reserve("NO_AVAILABILITY")
        self.assertEqual(r["status"], STATUS_REJECTED)
        self.assertEqual(r.get("error"), "NO_AVAILABILITY")
        _assert_native_envelope(self, r)

    def test_constraint_mismatch(self):
        r = self._reserve("CONSTRAINT_MISMATCH")
        self.assertEqual(r.get("error"), "CONSTRAINT_MISMATCH")
        _assert_native_envelope(self, r)

    def test_business_rejected(self):
        r = self._reserve("BUSINESS_REJECTED")
        self.assertEqual(r["status"], STATUS_REJECTED)
        self.assertEqual(r.get("error"), "BUSINESS_REJECTED")
        _assert_native_envelope(self, r)

    def test_partial_result(self):
        r = self._reserve("PARTIAL_RESULT")
        self.assertEqual(r["status"], STATUS_CONFIRMED)
        self.assertTrue(r["actual"].get("partial") or r.get("reason") == "PARTIAL_RESULT")
        _assert_native_envelope(self, r)

    def test_pending(self):
        r = self._reserve("PENDING")
        self.assertEqual(r["status"], STATUS_PENDING)
        _assert_native_envelope(self, r)

    def test_technical_error(self):
        r = self._reserve("TECHNICAL_ERROR")
        self.assertFalse(r["transport_ok"])
        self.assertEqual(r.get("error"), "TECHNICAL_ERROR")
        _assert_native_envelope(self, r)

    def test_timeout_immediate(self):
        import time
        t0 = time.monotonic()
        r = self._reserve("TIMEOUT")
        elapsed = time.monotonic() - t0
        self.assertLess(elapsed, 1.0, "TIMEOUT must not sleep long")
        self.assertFalse(r["transport_ok"])
        self.assertEqual(r.get("error"), "TIMEOUT")
        _assert_native_envelope(self, r)

    def test_duplicate_idempotent_scenario(self):
        r1 = self._reserve("DUPLICATE_IDEMPOTENT", idempotency_key="idem-dup")
        r2 = self._reserve("DUPLICATE_IDEMPOTENT", idempotency_key="idem-dup")
        self.assertEqual(r1["reservation_id"], r2["reservation_id"])
        self.assertTrue(r2.get("idempotent_replay"))
        _assert_native_envelope(self, r2)

    def test_golden_technical_success_business_mismatch(self):
        """Golden: 19:00/4/PRIVATE_ROOM → CONFIRMED actual 19:30/4/TABLE. No ABIS MISMATCH label."""
        r = self.engine.reserve(
            date="2026-09-12",
            time="19:00",
            party_size=4,
            seating_type=SEATING_PRIVATE_ROOM,
            customer_reference="TEST-CUST-GOLDEN",
            idempotency_key="idem-golden",
            test_scenario="TECHNICAL_SUCCESS_BUSINESS_MISMATCH",
        )
        _assert_native_envelope(self, r)
        self.assertTrue(r["transport_ok"])
        self.assertEqual(r["status"], STATUS_CONFIRMED)
        self.assertEqual(r["requested"]["time"], "19:00")
        self.assertEqual(r["requested"]["party_size"], 4)
        self.assertEqual(r["requested"]["seating_type"], SEATING_PRIVATE_ROOM)
        self.assertEqual(r["actual"]["time"], "19:30")
        self.assertEqual(r["actual"]["party_size"], 4)
        self.assertEqual(r["actual"]["seating_type"], SEATING_TABLE)
        self.assertTrue(str(r["reservation_id"]).startswith("TEST-RSV-"))
        # Explicitly no ABIS mismatch labeling
        blob = json.dumps(r)
        self.assertNotIn("ABIS_MISMATCH", blob)
        self.assertNotIn("abis_mismatch", blob)
        self.assertNotIn("abis_outcome", blob)
        self.assertNotIn("abis_verdict", blob)

    def test_technical_success_time_mismatch_only(self):
        r = self.engine.reserve(
            date="2026-09-12",
            time="19:00",
            party_size=4,
            seating_type=SEATING_PRIVATE_ROOM,
            customer_reference="TEST-CUST-TIME",
            idempotency_key="idem-time",
            test_scenario="TECHNICAL_SUCCESS_TIME_MISMATCH",
        )
        self.assertEqual(r["status"], STATUS_CONFIRMED)
        self.assertEqual(r["actual"]["time"], "19:30")
        self.assertEqual(r["actual"]["seating_type"], SEATING_PRIVATE_ROOM)

    def test_technical_success_seating_mismatch_only(self):
        r = self.engine.reserve(
            date="2026-09-12",
            time="19:00",
            party_size=4,
            seating_type=SEATING_PRIVATE_ROOM,
            customer_reference="TEST-CUST-SEAT",
            idempotency_key="idem-seat",
            test_scenario="TECHNICAL_SUCCESS_SEATING_MISMATCH",
        )
        self.assertEqual(r["status"], STATUS_CONFIRMED)
        self.assertEqual(r["actual"]["time"], "19:00")
        self.assertEqual(r["actual"]["seating_type"], SEATING_TABLE)


class TestHttpApi(unittest.TestCase):
    """Req: stdlib http.server routes + in-process handle_request."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = ReservationEngine(data_dir=self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_health(self):
        code, body = handle_request(self.engine, "GET", "/health", {})
        self.assertEqual(code, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["semantic_authority"], "NONE")

    def test_availability_http(self):
        q = urlencode({"date": "2026-09-12", "party_size": 4, "seating_type": SEATING_PRIVATE_ROOM})
        code, body = handle_request(self.engine, "GET", f"/availability?{q}", {})
        self.assertEqual(code, 200)
        _assert_native_envelope(self, body)
        self.assertTrue(any(s["time"] == "18:00" for s in body.get("slots", [])))

    def test_reservations_crud_via_api(self):
        payload = {
            "date": "2026-09-12",
            "time": "18:00",
            "party_size": 2,
            "seating_type": SEATING_PRIVATE_ROOM,
            "customer_reference": "TEST-CUST-HTTP",
            "idempotency_key": "idem-http-1",
        }
        code, body = handle_request(
            self.engine, "POST", "/reservations", {"Content-Type": "application/json"},
            json.dumps(payload).encode(),
        )
        self.assertEqual(code, 201)
        rid = body["reservation_id"]
        code, g = handle_request(self.engine, "GET", f"/reservations/{rid}", {})
        self.assertEqual(code, 200)
        code, m = handle_request(
            self.engine, "PATCH", f"/reservations/{rid}", {},
            json.dumps({"party_size": 3}).encode(),
        )
        self.assertEqual(code, 200)
        self.assertEqual(m["actual"]["party_size"], 3)
        code, c = handle_request(self.engine, "DELETE", f"/reservations/{rid}", {})
        self.assertEqual(code, 200)
        self.assertEqual(c["status"], STATUS_CANCELLED)

    def test_scenario_via_header(self):
        payload = {
            "date": "2026-09-12",
            "time": "18:00",
            "party_size": 2,
            "seating_type": SEATING_PRIVATE_ROOM,
            "customer_reference": "TEST-CUST-HDR",
            "idempotency_key": "idem-hdr",
        }
        code, body = handle_request(
            self.engine,
            "POST",
            "/reservations",
            {"X-CRS-Test-Scenario": "BUSINESS_REJECTED"},
            json.dumps(payload).encode(),
        )
        self.assertEqual(body.get("error"), "BUSINESS_REJECTED")
        self.assertEqual(body.get("test_scenario"), "BUSINESS_REJECTED")
        _assert_native_envelope(self, body)

    def test_test_only_scenario_endpoint(self):
        code, body = handle_request(
            self.engine,
            "POST",
            "/_test/scenario",
            {},
            json.dumps({"test_scenario": "PENDING"}).encode(),
        )
        self.assertEqual(code, 200)
        self.assertTrue(body.get("test_only"))


class TestLiveServer(unittest.TestCase):
    """Smoke: ThreadingHTTPServer round-trip."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = ReservationEngine(data_dir=self.tmp.name)
        handler = make_handler(self.engine)
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.httpd.crs_quiet = True  # type: ignore[attr-defined]
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.tmp.cleanup()

    def test_health_live(self):
        with urlopen(f"http://127.0.0.1:{self.port}/health", timeout=2) as resp:
            data = json.loads(resp.read().decode())
        self.assertTrue(data["ok"])

    def test_reserve_live(self):
        body = json.dumps({
            "date": "2026-09-12",
            "time": "20:00",
            "party_size": 2,
            "seating_type": SEATING_PRIVATE_ROOM,
            "customer_reference": "TEST-CUST-LIVE",
            "idempotency_key": "idem-live",
            "test_scenario": "NORMAL_SUCCESS",
        }).encode()
        req = Request(
            f"http://127.0.0.1:{self.port}/reservations",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode())
        _assert_native_envelope(self, data)
        self.assertEqual(data["status"], STATUS_CONFIRMED)


class TestNoAbisKeysEverywhere(unittest.TestCase):
    def test_forbid_list_complete(self):
        for k in ("abis_outcome", "abis_verdict", "abis_mismatch", "outcome_verification"):
            self.assertIn(k, FORBIDDEN_ABIS_KEYS)


if __name__ == "__main__":
    unittest.main()
