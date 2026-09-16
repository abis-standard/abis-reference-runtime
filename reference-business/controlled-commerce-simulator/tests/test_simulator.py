"""Controlled Commerce Simulator unit tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

CSS_SRC = Path(__file__).resolve().parents[1] / "src"
if str(CSS_SRC) not in sys.path:
    sys.path.insert(0, str(CSS_SRC))

from css.engine import CommerceEngine  # noqa: E402
from css.models import STATUS_ORDER_SUBMITTED  # noqa: E402


class TestCommerceSimulator(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = CommerceEngine()

    def test_submit_order_success(self) -> None:
        result = self.engine.submit_order("SKU-DEMO-001", 2, idempotency_key="css-idem-001")
        self.assertTrue(result["transport_ok"])
        self.assertEqual(result["status"], STATUS_ORDER_SUBMITTED)
        self.assertIsNotNone(result.get("order_id"))

    def test_idempotency(self) -> None:
        first = self.engine.submit_order("SKU-DEMO-001", 1, idempotency_key="css-idem-002")
        second = self.engine.submit_order("SKU-DEMO-001", 1, idempotency_key="css-idem-002")
        self.assertEqual(first["order_id"], second["order_id"])

    def test_unknown_sku(self) -> None:
        result = self.engine.submit_order("SKU-UNKNOWN", 1, test_scenario="UNKNOWN_SKU")
        self.assertFalse(result["transport_ok"])


if __name__ == "__main__":
    unittest.main()
