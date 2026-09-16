"""Business Interaction Adapter protocol — implementation-level vertical boundary."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from abis_grp_runtime.connector import BusinessConnectorPort


class BusinessInteractionAdapter(ABC):
    """Maps a vertical interaction to validation, descriptor, and connector execution."""

    adapter_id: str
    vertical: str
    supported_operations: frozenset[str]
    default_execution_classes: frozenset[str]
    business_system_identifier: str
    business_system_classification: str = "EXTERNAL_BUSINESS_SYSTEM_TEST_DOUBLE"

    @abstractmethod
    def validate_structured_input(self, operation: str, structured_input: Mapping[str, Any]) -> None:
        """Raise AdapterValidationError when structured_input is invalid."""

    @abstractmethod
    def get_descriptor(self, operation: str) -> dict[str, Any]:
        """Return full Interaction Descriptor document for the operation."""

    @abstractmethod
    def get_connector(self) -> BusinessConnectorPort:
        ...

    def bind_operation(self, operation: str) -> str:
        """Map advertised operation to connector execute() operation string."""
        return operation.strip().lower()
