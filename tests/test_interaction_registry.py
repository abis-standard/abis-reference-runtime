"""Runtime Interaction Registry tests."""

from __future__ import annotations

import unittest

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.adapters.restaurant import RestaurantBusinessAdapter  # noqa: E402
from abis_grp_runtime.registry.factory import build_reference_registry  # noqa: E402
from abis_grp_runtime.registry.interaction_registry import (  # noqa: E402
    BusinessAdapterRegistration,
    RuntimeInteractionRegistry,
)
from css.engine import CommerceEngine  # noqa: E402
from crs.engine import ReservationEngine  # noqa: E402


class TestInteractionRegistry(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = build_reference_registry(
            ReservationEngine(data_dir="/tmp/abis-registry-test"),
            CommerceEngine(),
        )

    def test_published_interactions(self) -> None:
        published = self.registry.get_published()
        keys = {(entry.vertical, entry.operation) for entry in published}
        self.assertEqual(
            keys,
            {("restaurant", "reserve"), ("shopping", "submit_order")},
        )

    def test_implemented_equals_published_for_reference(self) -> None:
        self.assertEqual(len(self.registry.get_implemented()), len(self.registry.get_published()))

    def test_unpublished_not_in_profile(self) -> None:
        registry = RuntimeInteractionRegistry()
        adapter = RestaurantBusinessAdapter(ReservationEngine(data_dir="/tmp/abis-registry-unpub"))
        registry.register(
            BusinessAdapterRegistration(adapter=adapter, operation="reserve", published=False)
        )
        self.assertEqual(registry.get_published(), ())
        self.assertIsNone(registry.find_published("restaurant", "reserve"))

    def test_descriptor_path_on_entry(self) -> None:
        entry = self.registry.find_published("restaurant", "reserve")
        assert entry is not None
        self.assertEqual(
            entry.descriptor_path,
            "/v1/reference-profile/interactions/restaurant/reserve",
        )

    def test_validate_structured_input_delegates(self) -> None:
        self.registry.validate_structured_input(
            "shopping",
            "submit_order",
            {"sku_id": "SKU-DEMO-001", "quantity": 2},
        )


if __name__ == "__main__":
    unittest.main()
