"""Build the reference Runtime Interaction Registry."""

from __future__ import annotations

from typing import Any

from abis_grp_runtime.adapters.restaurant import RestaurantBusinessAdapter
from abis_grp_runtime.adapters.shopping import ShoppingBusinessAdapter
from abis_grp_runtime.registry.interaction_registry import (
    BusinessAdapterRegistration,
    RuntimeInteractionRegistry,
    set_active_registry,
)


def build_reference_registry(crs_engine: Any, css_engine: Any) -> RuntimeInteractionRegistry:
    registry = RuntimeInteractionRegistry()
    registry.register(
        BusinessAdapterRegistration(
            adapter=RestaurantBusinessAdapter(crs_engine),
            operation="reserve",
            published=True,
        )
    )
    registry.register(
        BusinessAdapterRegistration(
            adapter=ShoppingBusinessAdapter(css_engine),
            operation="submit_order",
            published=True,
        )
    )
    set_active_registry(registry)
    from abis_grp_runtime.gateway.execution_surface import _refresh_aliases

    _refresh_aliases()
    return registry
