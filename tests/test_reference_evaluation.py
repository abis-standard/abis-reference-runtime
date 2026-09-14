"""Reference evaluation tests — EXACT_MATCH only for Public v0.1."""

from __future__ import annotations

import tempfile
import unittest

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.outcome_testbed import (  # noqa: E402
    EVALUATION_MATCH,
    ExpectedState,
    OutcomeResultPatternTestbed,
)
from abis_grp_runtime.outcome_testbed.patterns import PATTERN_EXACT_MATCH  # noqa: E402
from crs.engine import ReservationEngine  # noqa: E402


class TestReferenceEvaluation(unittest.TestCase):
    def test_exact_match(self) -> None:
        testbed = OutcomeResultPatternTestbed()
        expected = ExpectedState(
            date="2026-09-12",
            time="20:00",
            party_size=4,
            seating_type="PRIVATE_ROOM",
        )
        native = {
            "transport_ok": True,
            "status": "CONFIRMED",
            "actual": {
                "date": "2026-09-12",
                "time": "20:00",
                "party_size": 4,
                "seating_type": "PRIVATE_ROOM",
                "status": "CONFIRMED",
            },
        }
        result, trace = testbed.evaluate(expected, native, correlation_id="ref-eval-001")
        self.assertEqual(result.evaluation, EVALUATION_MATCH)
        self.assertEqual(result.pattern, PATTERN_EXACT_MATCH)
        self.assertEqual(trace.to_dict()["semantic_authority"], "NONE")


class TestCrsNormalSuccess(unittest.TestCase):
    def test_crs_normal_success_via_engine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            engine = ReservationEngine(data_dir=tmp)
            native = engine.reserve(
                date="2026-09-12",
                time="20:00",
                party_size=4,
                seating_type="PRIVATE_ROOM",
                customer_reference="TEST-CUST-REFERENCE",
                idempotency_key="idem-reference-eval-001",
                test_scenario="NORMAL_SUCCESS",
            )
            testbed = OutcomeResultPatternTestbed()
            expected = ExpectedState(
                date="2026-09-12",
                time="20:00",
                party_size=4,
                seating_type="PRIVATE_ROOM",
            )
            result, _ = testbed.evaluate(expected, native, correlation_id="crs-normal")
            self.assertEqual(result.evaluation, EVALUATION_MATCH)
            self.assertEqual(native["status"], "CONFIRMED")


if __name__ == "__main__":
    unittest.main()
