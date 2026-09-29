"""Travel stay simulator — synthetic technical result only (not a real reservation)."""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

from abis_grp_runtime.connector import BusinessConnectorPort
from abis_grp_runtime.connectors.egress import ALLOWED_SIMULATOR_TARGET, SimulatorEgressFirewall
from abis_grp_runtime.native_result import NativeResultEnvelope

SIMULATOR_NATIVE_STATUS = "SIMULATED_TECHNICAL_SUCCESS"
CLASSIFICATION = "CONTROLLED_TRAVEL_STAY_SIMULATOR"


def _synthetic_stay_reference(client_reference: str, idempotency_key: str) -> str:
    digest = hashlib.sha256(f"{client_reference}:{idempotency_key}".encode()).hexdigest()
    return f"SYN-STAY-{digest[:16].upper()}"


class TravelStaySimulatorEngine:
    """In-process deterministic stay-reserve simulator."""

    def stay_reserve(self, ctx: Mapping[str, Any]) -> dict[str, Any]:
        stay = dict(ctx.get("stay") or {})
        occupancy = dict(ctx.get("occupancy") or {})
        client_reference = str(ctx.get("client_reference") or "")
        idempotency_key = str(ctx.get("idempotency_key") or client_reference or "idem-travel")
        return {
            "transport_ok": True,
            "status": SIMULATOR_NATIVE_STATUS,
            "stay_reference": _synthetic_stay_reference(client_reference, idempotency_key),
            "requested": {
                "check_in": stay.get("check_in"),
                "check_out": stay.get("check_out"),
                "rooms": occupancy.get("rooms"),
                "adults": occupancy.get("adults"),
                "children": occupancy.get("children"),
            },
            "business_system": "abis-demo-travel-stay-simulator",
            "classification": CLASSIFICATION,
            "semantic_authority": "NONE",
            "offer_reference_supplied": bool(str(ctx.get("selected_offer_reference") or "").strip()),
        }


def travel_dict_to_native_envelope(result: Mapping[str, Any], *, operation: str) -> NativeResultEnvelope:
    transport_ok = bool(result.get("transport_ok"))
    stay_ref = result.get("stay_reference")
    return NativeResultEnvelope(
        technical_status="TRANSPORT_OK" if transport_ok else "TRANSPORT_FAILED",
        external_status=str(result.get("status")) if result.get("status") is not None else None,
        external_identifier=str(stay_ref) if stay_ref else None,
        source="travel-stay-simulator",
        payload={
            "operation": operation,
            "simulator_native_result": {
                "classification": result.get("classification"),
                "business_system": result.get("business_system"),
                "semantic_authority": result.get("semantic_authority"),
                "offer_reference_supplied": result.get("offer_reference_supplied"),
                "requested": dict(result.get("requested") or {}),
            },
        },
    )


class TravelStaySimulatorConnector(BusinessConnectorPort):
    connector_id = "travel-stay-simulator"

    def __init__(
        self,
        engine: TravelStaySimulatorEngine | None = None,
        *,
        target: str = ALLOWED_SIMULATOR_TARGET,
        firewall: SimulatorEgressFirewall | None = None,
    ) -> None:
        self._firewall = firewall or SimulatorEgressFirewall()
        self._firewall.require_simulator_target(target)
        self._engine = engine or TravelStaySimulatorEngine()
        self._target = target

    def execute(self, operation: str, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        op = operation.strip().lower()
        if op != "stay_reserve":
            return NativeResultEnvelope(
                technical_status="TRANSPORT_FAILED",
                external_status=None,
                source=self.connector_id,
                payload={"operation": operation, "error": "unsupported_operation"},
            )
        result = self._engine.stay_reserve(operation_context)
        return travel_dict_to_native_envelope(result, operation=op)
