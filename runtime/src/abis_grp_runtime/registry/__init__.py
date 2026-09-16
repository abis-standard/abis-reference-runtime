"""Runtime Interaction Registry."""

from abis_grp_runtime.registry.interaction_registry import (
    BusinessAdapterRegistration,
    RegisteredInteraction,
    RuntimeInteractionRegistry,
    get_active_registry,
    require_active_registry,
    set_active_registry,
)

__all__ = [
    "BusinessAdapterRegistration",
    "RegisteredInteraction",
    "RuntimeInteractionRegistry",
    "get_active_registry",
    "require_active_registry",
    "set_active_registry",
]
