"""Generic Business System connector interface — no domain-specific policy."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from abis_grp_runtime.native_result import NativeResultEnvelope


class BusinessConnectorPort(ABC):
    """
    Generic connector interface for future Business Systems.

    Domain-neutral operation names only — no restaurant-specific policy embedded.
    """

    connector_id: str = "abstract"

    @abstractmethod
    def check_availability(self, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        ...

    @abstractmethod
    def reserve(self, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        ...

    @abstractmethod
    def modify(self, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        ...

    @abstractmethod
    def cancel(self, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        ...


class NullConnector(BusinessConnectorPort):
    """Null executor — no external network or Business System mutation."""

    connector_id = "null"

    def check_availability(self, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        return NativeResultEnvelope(
            technical_status="NULL_EXECUTOR",
            external_status=None,
            source=self.connector_id,
            payload={"operation": "check_availability", "mutated": False},
        )

    def reserve(self, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        return NativeResultEnvelope(
            technical_status="NULL_EXECUTOR",
            external_status=None,
            source=self.connector_id,
            payload={"operation": "reserve", "mutated": False},
        )

    def modify(self, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        return NativeResultEnvelope(
            technical_status="NULL_EXECUTOR",
            external_status=None,
            source=self.connector_id,
            payload={"operation": "modify", "mutated": False},
        )

    def cancel(self, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        return NativeResultEnvelope(
            technical_status="NULL_EXECUTOR",
            external_status=None,
            source=self.connector_id,
            payload={"operation": "cancel", "mutated": False},
        )


class FixtureConnector(BusinessConnectorPort):
    """Fixture executor — local deterministic observations only."""

    connector_id = "fixture"

    def check_availability(self, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        return NativeResultEnvelope(
            technical_status="FIXTURE_OK",
            external_status="AVAILABLE",
            source=self.connector_id,
            payload={"operation": "check_availability", "fixture": True, "mutated": False},
        )

    def reserve(self, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        return NativeResultEnvelope(
            technical_status="FIXTURE_OK",
            external_status="CONFIRMED",
            external_identifier="FIX-001",
            source=self.connector_id,
            payload={"operation": "reserve", "fixture": True, "mutated": False},
        )

    def modify(self, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        return NativeResultEnvelope(
            technical_status="FIXTURE_OK",
            external_status="MODIFIED",
            source=self.connector_id,
            payload={"operation": "modify", "fixture": True, "mutated": False},
        )

    def cancel(self, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        return NativeResultEnvelope(
            technical_status="FIXTURE_OK",
            external_status="CANCELLED",
            source=self.connector_id,
            payload={"operation": "cancel", "fixture": True, "mutated": False},
        )
