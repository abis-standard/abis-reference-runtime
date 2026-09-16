"""Commerce Connector — Controlled Commerce Simulator only."""

from __future__ import annotations

from typing import Any, Mapping

from abis_grp_runtime.connector import BusinessConnectorPort
from abis_grp_runtime.connectors.egress import ALLOWED_SIMULATOR_TARGET, SimulatorEgressFirewall
from abis_grp_runtime.native_result import NativeResultEnvelope


def css_dict_to_native_envelope(css: Mapping[str, Any], *, operation: str) -> NativeResultEnvelope:
    transport_ok = bool(css.get("transport_ok"))
    return NativeResultEnvelope(
        technical_status="TRANSPORT_OK" if transport_ok else "TRANSPORT_FAILED",
        external_status=css.get("status"),
        external_identifier=css.get("order_id"),
        source="commerce-simulator",
        payload={
            "operation": operation,
            "css_native_result": dict(css),
            "business_system": css.get("business_system"),
            "classification": css.get("classification"),
            "semantic_authority": css.get("semantic_authority"),
        },
    )


class CommerceSimulatorConnector(BusinessConnectorPort):
    """Minimum Commerce Connector for CSS invocation."""

    connector_id = "commerce-simulator"

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
        if op != "submit_order":
            return NativeResultEnvelope(
                technical_status="TRANSPORT_FAILED",
                external_status=None,
                source=self.connector_id,
                payload={"operation": operation, "error": "unsupported_operation"},
            )
        ctx = dict(operation_context)
        css = self._engine.submit_order(
            sku_id=str(ctx.get("sku_id", "")),
            quantity=int(ctx.get("quantity", 0)),
            idempotency_key=str(ctx.get("idempotency_key") or "") or None,
            test_scenario=ctx.get("test_scenario"),
        )
        return css_dict_to_native_envelope(css, operation="submit_order")
