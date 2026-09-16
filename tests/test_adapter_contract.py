"""Business Interaction Adapter contract tests."""

from __future__ import annotations

import unittest

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.adapters.errors import AdapterValidationError  # noqa: E402
from abis_grp_runtime.adapters.protocol import BusinessInteractionAdapter  # noqa: E402
from abis_grp_runtime.adapters.restaurant import RestaurantBusinessAdapter  # noqa: E402
from abis_grp_runtime.adapters.shopping import ShoppingBusinessAdapter  # noqa: E402
from css.engine import CommerceEngine  # noqa: E402
from crs.engine import ReservationEngine  # noqa: E402


class TestAdapterContract(unittest.TestCase):
    def test_protocol_is_abc(self) -> None:
        self.assertTrue(issubclass(BusinessInteractionAdapter, BusinessInteractionAdapter))
        abstract = set(BusinessInteractionAdapter.__abstractmethods__)
        self.assertEqual(
            abstract,
            {"validate_structured_input", "get_descriptor", "get_connector"},
        )

    def test_restaurant_adapter_metadata(self) -> None:
        adapter = RestaurantBusinessAdapter(ReservationEngine(data_dir="/tmp/abis-adapter-test"))
        self.assertEqual(adapter.adapter_id, "restaurant")
        self.assertEqual(adapter.vertical, "restaurant")
        self.assertEqual(adapter.supported_operations, frozenset({"reserve"}))

    def test_shopping_adapter_metadata(self) -> None:
        adapter = ShoppingBusinessAdapter(CommerceEngine())
        self.assertEqual(adapter.adapter_id, "shopping")
        self.assertEqual(adapter.vertical, "shopping")
        self.assertEqual(adapter.supported_operations, frozenset({"submit_order"}))

    def test_restaurant_validation_requires_fields(self) -> None:
        adapter = RestaurantBusinessAdapter(ReservationEngine(data_dir="/tmp/abis-adapter-test"))
        with self.assertRaises(AdapterValidationError):
            adapter.validate_structured_input("reserve", {"date": "2026-09-12"})

    def test_shopping_rejects_payment_fields(self) -> None:
        adapter = ShoppingBusinessAdapter(CommerceEngine())
        with self.assertRaises(AdapterValidationError):
            adapter.validate_structured_input(
                "submit_order",
                {"sku_id": "SKU-DEMO-001", "quantity": 1, "card_number": "4111111111111111"},
            )

    def test_connector_execute_only(self) -> None:
        adapter = RestaurantBusinessAdapter(ReservationEngine(data_dir="/tmp/abis-adapter-test"))
        connector = adapter.get_connector()
        self.assertTrue(hasattr(connector, "execute"))
        for forbidden in ("reserve", "modify", "cancel", "check_availability"):
            self.assertFalse(hasattr(connector, forbidden))


if __name__ == "__main__":
    unittest.main()
