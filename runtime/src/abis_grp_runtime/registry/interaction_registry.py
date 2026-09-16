"""Runtime Interaction Registry — publication source of truth."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from abis_grp_runtime.adapters.protocol import BusinessInteractionAdapter
from abis_grp_runtime.descriptor.constants import descriptor_path_for

_ACTIVE_REGISTRY: RuntimeInteractionRegistry | None = None


@dataclass(frozen=True)
class RegisteredInteraction:
    vertical: str
    operation: str
    execution_classes_allowed: frozenset[str]
    adapter_id: str
    published: bool
    invocation_method: str = "POST"
    business_system_identifier: str = ""
    business_system_classification: str = "EXTERNAL_BUSINESS_SYSTEM_TEST_DOUBLE"

    @property
    def invocation_path(self) -> str:
        return f"/v1/demo/{self.vertical}/invoke"

    @property
    def preflight_path(self) -> str:
        return f"/v1/demo/{self.vertical}/preflight"

    @property
    def descriptor_path(self) -> str:
        return descriptor_path_for(self.vertical, self.operation)

    def to_profile_dict(self) -> dict[str, Any]:
        return {
            "vertical": self.vertical,
            "operation": self.operation,
            "execution_classes_allowed": sorted(self.execution_classes_allowed),
            "invocation": {"method": self.invocation_method, "path": self.invocation_path},
            "descriptor_path": self.descriptor_path,
            "business_system": {
                "identifier": self.business_system_identifier,
                "classification": self.business_system_classification,
            },
        }


@dataclass(frozen=True)
class BusinessAdapterRegistration:
    adapter: BusinessInteractionAdapter
    operation: str
    published: bool = True


class RuntimeInteractionRegistry:
    """Registers adapters and exposes published interaction truth."""

    def __init__(self) -> None:
        self._entries: dict[tuple[str, str], tuple[BusinessInteractionAdapter, RegisteredInteraction]] = {}

    def register(self, registration: BusinessAdapterRegistration) -> None:
        adapter = registration.adapter
        operation = registration.operation.strip().lower()
        vertical = adapter.vertical.strip().lower()
        if operation not in adapter.supported_operations:
            raise ValueError(f"operation {operation} not supported by adapter {adapter.adapter_id}")
        entry = RegisteredInteraction(
            vertical=vertical,
            operation=operation,
            execution_classes_allowed=adapter.default_execution_classes,
            adapter_id=adapter.adapter_id,
            published=registration.published,
            business_system_identifier=adapter.business_system_identifier,
            business_system_classification=adapter.business_system_classification,
        )
        self._entries[(vertical, operation)] = (adapter, entry)

    def get_implemented(self) -> tuple[RegisteredInteraction, ...]:
        return tuple(entry for _, entry in sorted(self._entries.values(), key=lambda e: (e[1].vertical, e[1].operation)))

    def get_published(self) -> tuple[RegisteredInteraction, ...]:
        return tuple(entry for entry in self.get_implemented() if entry.published)

    def find(self, vertical: str, operation: str) -> RegisteredInteraction | None:
        key = (vertical.strip().lower(), operation.strip().lower())
        pair = self._entries.get(key)
        return pair[1] if pair else None

    def find_published(self, vertical: str, operation: str) -> RegisteredInteraction | None:
        entry = self.find(vertical, operation)
        return entry if entry and entry.published else None

    def get_adapter(self, vertical: str, operation: str) -> BusinessInteractionAdapter:
        key = (vertical.strip().lower(), operation.strip().lower())
        pair = self._entries.get(key)
        if pair is None:
            raise KeyError(f"interaction not registered: {vertical}/{operation}")
        return pair[0]

    def get_descriptor(self, vertical: str, operation: str) -> dict[str, Any]:
        entry = self.find_published(vertical, operation)
        if entry is None:
            raise KeyError(f"interaction not published: {vertical}/{operation}")
        adapter = self.get_adapter(vertical, operation)
        return adapter.get_descriptor(operation)

    def validate_structured_input(self, vertical: str, operation: str, structured_input: dict[str, Any]) -> None:
        adapter = self.get_adapter(vertical, operation)
        adapter.validate_structured_input(operation, structured_input)

    def published_verticals(self) -> frozenset[str]:
        return frozenset(entry.vertical for entry in self.get_published())

    def published_operations(self) -> frozenset[str]:
        return frozenset(entry.operation for entry in self.get_published())

    def is_advertised_invocation(self, vertical: str, operation: str, execution_class: str) -> bool:
        entry = self.find_published(vertical, operation)
        if entry is None:
            return False
        return execution_class.strip().upper() in entry.execution_classes_allowed


def set_active_registry(registry: RuntimeInteractionRegistry) -> None:
    global _ACTIVE_REGISTRY
    _ACTIVE_REGISTRY = registry


def get_active_registry() -> RuntimeInteractionRegistry | None:
    return _ACTIVE_REGISTRY


def require_active_registry() -> RuntimeInteractionRegistry:
    registry = get_active_registry()
    if registry is None:
        raise RuntimeError("Runtime Interaction Registry is not initialized")
    return registry
