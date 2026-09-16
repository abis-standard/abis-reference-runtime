"""Restaurant Connector — Controlled Reservation Simulator only."""

from __future__ import annotations

from typing import Any, Mapping

from abis_grp_runtime.connector import BusinessConnectorPort
from abis_grp_runtime.connectors.egress import ALLOWED_SIMULATOR_TARGET, SimulatorEgressFirewall
from abis_grp_runtime.native_result import NativeResultEnvelope


def crs_dict_to_native_envelope(crs: Mapping[str, Any], *, operation: str) -> NativeResultEnvelope:
    """Map CRS Native Result dict to Runtime NativeResultEnvelope without Outcome determination."""
    transport_ok = bool(crs.get("transport_ok"))
    return NativeResultEnvelope(
        technical_status="TRANSPORT_OK" if transport_ok else "TRANSPORT_FAILED",
        external_status=crs.get("status"),
        external_identifier=crs.get("reservation_id"),
        source="restaurant-simulator",
        payload={
            "operation": operation,
            "crs_native_result": dict(crs),
            "business_system": crs.get("business_system"),
            "classification": crs.get("classification"),
            "semantic_authority": crs.get("semantic_authority"),
        },
    )


class RestaurantSimulatorConnector(BusinessConnectorPort):
    """
    Minimum Restaurant Connector for CRS invocation.

    Does NOT determine ABIS Outcome, equivalence, mismatch, or Conformance.
    """

    connector_id = "restaurant-simulator"

    def __init__(
        self,
        engine: Any,
        *,
        target: str = ALLOWED_SIMULATOR_TARGET,
        firewall: SimulatorEgressFirewall | None = None,
    ) -> None:
        self._firewall = firewall or SimulatorEgressFirewall()
        self._firewall.require_simulator_target(target)
        self._engine = engine
        self._target = target

    def execute(self, operation: str, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        op = operation.strip().lower()
        ctx = dict(operation_context)
        if op == "check_availability":
            crs = self._engine.availability(
                date=str(ctx.get("date", "")),
                party_size=int(ctx.get("party_size", 0)),
                preferred_time=ctx.get("time"),
                seating_type=ctx.get("seating_type"),
                test_scenario=ctx.get("test_scenario"),
            )
            return crs_dict_to_native_envelope(crs, operation=op)
        if op == "reserve":
            crs = self._engine.reserve(**self._reserve_fields(ctx))
            return crs_dict_to_native_envelope(crs, operation=op)
        if op == "modify":
            reservation_id = str(ctx.get("reservation_id", ""))
            fields = {
                k: ctx[k]
                for k in ("date", "time", "party_size", "seating_type", "customer_reference", "status")
                if k in ctx
            }
            crs = self._engine.modify(reservation_id, fields, test_scenario=ctx.get("test_scenario"))
            return crs_dict_to_native_envelope(crs, operation=op)
        if op == "cancel":
            reservation_id = str(ctx.get("reservation_id", ""))
            crs = self._engine.cancel(reservation_id, test_scenario=ctx.get("test_scenario"))
            return crs_dict_to_native_envelope(crs, operation=op)
        return NativeResultEnvelope(
            technical_status="TRANSPORT_FAILED",
            external_status=None,
            source=self.connector_id,
            payload={"operation": operation, "error": "unsupported_operation"},
        )

    def _reserve_fields(self, ctx: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "date": str(ctx.get("date", "")),
            "time": str(ctx.get("time", "")),
            "party_size": int(ctx.get("party_size", 0)),
            "seating_type": str(ctx.get("seating_type", "PRIVATE_ROOM")),
            "customer_reference": str(ctx.get("customer_reference") or "TEST-CUST-E2E"),
            "idempotency_key": str(ctx.get("idempotency_key") or ctx.get("correlation_id") or "idem-e2e"),
            "test_scenario": ctx.get("test_scenario"),
        }
