"""Generic Business System connector interface — no domain-specific policy."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from abis_grp_runtime.native_result import NativeResultEnvelope


class BusinessConnectorPort(ABC):
    """
    Generic connector interface for Business Systems.

    Domain-neutral execute(operation, context) only at the shared contract boundary.
    """

    connector_id: str = "abstract"

    @abstractmethod
    def execute(self, operation: str, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        ...


class NullConnector(BusinessConnectorPort):
    """Null executor — no external network or Business System mutation."""

    connector_id = "null"

    def execute(self, operation: str, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        return NativeResultEnvelope(
            technical_status="NULL_EXECUTOR",
            external_status=None,
            source=self.connector_id,
            payload={"operation": operation, "mutated": False},
        )


class FixtureConnector(BusinessConnectorPort):
    """Fixture executor — local deterministic observations only."""

    connector_id = "fixture"

    def execute(self, operation: str, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        op = operation.strip().lower()
        if op == "check_availability":
            return NativeResultEnvelope(
                technical_status="FIXTURE_OK",
                external_status="AVAILABLE",
                source=self.connector_id,
                payload={"operation": op, "fixture": True, "mutated": False},
            )
        if op == "reserve":
            return NativeResultEnvelope(
                technical_status="FIXTURE_OK",
                external_status="CONFIRMED",
                external_identifier="FIX-001",
                source=self.connector_id,
                payload={"operation": op, "fixture": True, "mutated": False},
            )
        if op == "modify":
            return NativeResultEnvelope(
                technical_status="FIXTURE_OK",
                external_status="MODIFIED",
                source=self.connector_id,
                payload={"operation": op, "fixture": True, "mutated": False},
            )
        if op == "cancel":
            return NativeResultEnvelope(
                technical_status="FIXTURE_OK",
                external_status="CANCELLED",
                source=self.connector_id,
                payload={"operation": op, "fixture": True, "mutated": False},
            )
        if op == "submit_order":
            return NativeResultEnvelope(
                technical_status="FIXTURE_OK",
                external_status="ORDER_SUBMITTED",
                external_identifier="FIX-ORD-001",
                source=self.connector_id,
                payload={"operation": op, "fixture": True, "mutated": False},
            )
        return NativeResultEnvelope(
            technical_status="NULL_EXECUTOR",
            external_status=None,
            source=self.connector_id,
            payload={"operation": operation, "mutated": False},
        )
