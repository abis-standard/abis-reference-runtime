"""Reference execution surface — canonical public gateway truth (implementation-level, not normative ABIS)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PUBLIC_VERTICALS: frozenset[str] = frozenset({"restaurant"})
PUBLIC_OPERATIONS: frozenset[str] = frozenset({"reserve"})
PUBLIC_EXECUTION_CLASSES: frozenset[str] = frozenset({"CONTROLLED_SIMULATOR"})

# Implementation-level surface revision — not ABIS semantic/conformance versioning.
EXECUTION_SURFACE_REVISION = "restaurant-reserve-1"

# Historical gateway validation aliases — derived from the same surface definition.
ALLOWED_VERTICALS_M206B = PUBLIC_VERTICALS
ALLOWED_OPERATIONS = PUBLIC_OPERATIONS
ALLOWED_EXECUTION_CLASSES = PUBLIC_EXECUTION_CLASSES


@dataclass(frozen=True)
class AdvertisedInteraction:
    vertical: str
    operation: str
    execution_classes_allowed: frozenset[str]
    invocation_method: str = "POST"

    @property
    def invocation_path(self) -> str:
        return f"/v1/demo/{self.vertical}/invoke"

    def to_dict(self) -> dict[str, Any]:
        return {
            "vertical": self.vertical,
            "operation": self.operation,
            "execution_classes_allowed": sorted(self.execution_classes_allowed),
            "invocation": {
                "method": self.invocation_method,
                "path": self.invocation_path,
            },
        }


def reference_execution_surface() -> tuple[AdvertisedInteraction, ...]:
    """Canonical advertised interactions for the public gateway."""
    interactions: list[AdvertisedInteraction] = []
    for vertical in sorted(PUBLIC_VERTICALS):
        for operation in sorted(PUBLIC_OPERATIONS):
            interactions.append(
                AdvertisedInteraction(
                    vertical=vertical,
                    operation=operation,
                    execution_classes_allowed=PUBLIC_EXECUTION_CLASSES,
                )
            )
    return tuple(interactions)


def advertised_interactions() -> list[dict[str, Any]]:
    return [item.to_dict() for item in reference_execution_surface()]


def find_advertised_interaction(vertical: str, operation: str) -> AdvertisedInteraction | None:
    vertical_norm = vertical.strip().lower()
    operation_norm = operation.strip().lower()
    for item in reference_execution_surface():
        if item.vertical == vertical_norm and item.operation == operation_norm:
            return item
    return None


def is_advertised_invocation(vertical: str, operation: str, execution_class: str) -> bool:
    matched = find_advertised_interaction(vertical, operation)
    if matched is None:
        return False
    return execution_class.strip().upper() in matched.execution_classes_allowed
