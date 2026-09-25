"""Reference execution surface — registry-backed public gateway truth."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from abis_grp_runtime.registry.interaction_registry import RegisteredInteraction, require_active_registry

EXECUTION_SURFACE_REVISION = "reference-execution-surface-5"
PUBLIC_EXECUTION_CLASSES: frozenset[str] = frozenset(
    {"CONTROLLED_SIMULATOR", "AUTHORIZED_NON_PRODUCTION"}
)


@dataclass(frozen=True)
class AdvertisedInteraction:
    vertical: str
    operation: str
    execution_classes_allowed: frozenset[str]
    invocation_method: str = "POST"
    descriptor_path: str = ""
    business_system_identifier: str = ""
    business_system_classification: str = "EXTERNAL_BUSINESS_SYSTEM_TEST_DOUBLE"

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
            "descriptor_path": self.descriptor_path,
            "business_system": {
                "identifier": self.business_system_identifier,
                "classification": self.business_system_classification,
            },
        }


def _from_registered(entry: RegisteredInteraction) -> AdvertisedInteraction:
    return AdvertisedInteraction(
        vertical=entry.vertical,
        operation=entry.operation,
        execution_classes_allowed=entry.execution_classes_allowed,
        invocation_method=entry.invocation_method,
        descriptor_path=entry.descriptor_path,
        business_system_identifier=entry.business_system_identifier,
        business_system_classification=entry.business_system_classification,
    )


def reference_execution_surface() -> tuple[AdvertisedInteraction, ...]:
    registry = require_active_registry()
    return tuple(_from_registered(entry) for entry in registry.get_published())


def advertised_interactions() -> list[dict[str, Any]]:
    return [item.to_dict() for item in reference_execution_surface()]


def find_advertised_interaction(vertical: str, operation: str) -> AdvertisedInteraction | None:
    registry = require_active_registry()
    entry = registry.find_published(vertical, operation)
    return _from_registered(entry) if entry else None


def is_advertised_invocation(vertical: str, operation: str, execution_class: str) -> bool:
    registry = require_active_registry()
    return registry.is_advertised_invocation(vertical, operation, execution_class)


def published_verticals() -> frozenset[str]:
    return require_active_registry().published_verticals()


def published_operations() -> frozenset[str]:
    return require_active_registry().published_operations()


# Historical gateway validation aliases — derived from registry publication state.
def _refresh_aliases() -> None:
    global ALLOWED_VERTICALS_M206B, ALLOWED_OPERATIONS
    registry = require_active_registry()
    ALLOWED_VERTICALS_M206B = registry.published_verticals()
    ALLOWED_OPERATIONS = registry.published_operations()


ALLOWED_VERTICALS_M206B: frozenset[str] = frozenset()
ALLOWED_OPERATIONS: frozenset[str] = frozenset()
ALLOWED_EXECUTION_CLASSES = PUBLIC_EXECUTION_CLASSES
