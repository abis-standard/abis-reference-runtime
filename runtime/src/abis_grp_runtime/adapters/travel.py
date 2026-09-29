"""Travel stay reserve — provider-neutral Business Interaction Adapter."""

from __future__ import annotations

from datetime import date
from typing import Any, Mapping

from abis_grp_runtime.adapters._validation import (
    reject_forbidden_keys,
    reject_unknown_keys,
    reject_url_like_values,
    require_fields,
)
from abis_grp_runtime.adapters.errors import AdapterValidationError
from abis_grp_runtime.adapters.protocol import BusinessInteractionAdapter
from abis_grp_runtime.connector import BusinessConnectorPort
from abis_grp_runtime.connectors.travel_stay_simulator import TravelStaySimulatorConnector
from abis_grp_runtime.descriptor.builder import build_descriptor
from abis_grp_runtime.execution import ExecutionClass

TRAVEL_ALLOWED_INPUT = frozenset(
    {
        "stay",
        "occupancy",
        "holder",
        "guests",
        "selected_offer_reference",
        "client_reference",
        "idempotency_key",
        "test_scenario",
        "semantic_refs",
        "_test_scenario_override",
    }
)

TRAVEL_FORBIDDEN_INPUT = frozenset(
    {
        "email",
        "phone",
        "payment_token",
        "card_number",
        "passport",
        "rate_key",
        "ratekey",
    }
)

TRAVEL_STRUCTURED_INPUT_SPEC: dict[str, Any] = {
    "required_fields": [
        "stay",
        "occupancy",
        "holder",
        "guests",
        "selected_offer_reference",
        "client_reference",
    ],
    "optional_fields": ["idempotency_key", "test_scenario", "semantic_refs"],
    "field_types": {
        "stay": "object",
        "occupancy": "object",
        "holder": "object",
        "guests": "array",
        "selected_offer_reference": "string",
        "client_reference": "string",
        "idempotency_key": "string",
        "test_scenario": "string",
        "semantic_refs": "object",
    },
}


def _parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise AdapterValidationError("stay dates must be ISO YYYY-MM-DD") from None


def _validate_guests(guests: Any, *, adults: int) -> None:
    if not isinstance(guests, list) or not guests:
        raise AdapterValidationError("guests must be a non-empty array")
    ad_count = 0
    for item in guests:
        if not isinstance(item, dict):
            raise AdapterValidationError("guest entries must be objects")
        reject_unknown_keys(
            item,
            frozenset({"room_id", "type", "name", "surname"}),
        )
        require_fields(item, ("room_id", "type", "name", "surname"))
        if str(item.get("type", "")).strip().upper() == "AD":
            ad_count += 1
    if ad_count < adults:
        raise AdapterValidationError("guests must include at least occupancy.adults adult entries")


class TravelStayReserveAdapter(BusinessInteractionAdapter):
    adapter_id = "travel"
    vertical = "travel"
    supported_operations = frozenset({"stay_reserve"})
    default_execution_classes = frozenset({"CONTROLLED_SIMULATOR"})
    business_system_identifier = "abis-demo-travel-stay-simulator"

    def __init__(self) -> None:
        self._simulator_connector = TravelStaySimulatorConnector()

    def validate_structured_input(self, operation: str, structured_input: Mapping[str, Any]) -> None:
        if operation.strip().lower() != "stay_reserve":
            raise AdapterValidationError(f"unsupported operation: {operation}")
        if not isinstance(structured_input, dict):
            raise AdapterValidationError("structured_input must be an object")
        data = dict(structured_input)
        reject_forbidden_keys(data, TRAVEL_FORBIDDEN_INPUT)
        reject_unknown_keys(data, TRAVEL_ALLOWED_INPUT)
        reject_url_like_values(data)

        stay = data.get("stay")
        occupancy = data.get("occupancy")
        holder = data.get("holder")
        if not isinstance(stay, dict):
            raise AdapterValidationError("stay must be an object")
        if not isinstance(occupancy, dict):
            raise AdapterValidationError("occupancy must be an object")
        if not isinstance(holder, dict):
            raise AdapterValidationError("holder must be an object")

        reject_unknown_keys(stay, frozenset({"check_in", "check_out"}))
        reject_unknown_keys(occupancy, frozenset({"rooms", "adults", "children"}))
        reject_unknown_keys(holder, frozenset({"name", "surname"}))
        require_fields(stay, ("check_in", "check_out"))
        require_fields(occupancy, ("rooms", "adults", "children"))
        require_fields(holder, ("name", "surname"))

        check_in = _parse_iso_date(str(stay["check_in"]))
        check_out = _parse_iso_date(str(stay["check_out"]))
        if check_out <= check_in:
            raise AdapterValidationError("check_out must be after check_in")

        try:
            rooms = int(occupancy["rooms"])
            adults = int(occupancy["adults"])
            children = int(occupancy["children"])
        except (TypeError, ValueError):
            raise AdapterValidationError("occupancy rooms/adults/children must be integers") from None
        if rooms < 1:
            raise AdapterValidationError("occupancy.rooms must be >= 1")
        if adults < 1:
            raise AdapterValidationError("occupancy.adults must be >= 1")
        if children < 0:
            raise AdapterValidationError("occupancy.children must be >= 0")

        offer_ref = str(data.get("selected_offer_reference") or "").strip()
        if not offer_ref:
            raise AdapterValidationError("selected_offer_reference must be non-empty")
        client_reference = str(data.get("client_reference") or "").strip()
        if not client_reference:
            raise AdapterValidationError("client_reference must be non-empty")

        _validate_guests(data.get("guests"), adults=adults)

    def get_descriptor(self, operation: str) -> dict[str, Any]:
        if operation.strip().lower() != "stay_reserve":
            raise AdapterValidationError(f"unsupported operation: {operation}")
        descriptor = build_descriptor(
            vertical=self.vertical,
            operation="stay_reserve",
            execution_classes_allowed=self.default_execution_classes,
            structured_input=TRAVEL_STRUCTURED_INPUT_SPEC,
            business_system_identifier=self.business_system_identifier,
            business_system_classification=self.business_system_classification,
        )
        descriptor["implementation_maturity"] = "DEVELOPER_PREVIEW"
        descriptor["external_provider_execution"] = "NOT_IMPLEMENTED"
        descriptor["notes"] = (
            "CONTROLLED_SIMULATOR only in this release phase. "
            "Native Result does not determine Business Outcome."
        )
        return descriptor

    def get_connector(self) -> BusinessConnectorPort:
        return self._simulator_connector

    def get_connector_for_execution_class(self, execution_class: str) -> BusinessConnectorPort:
        normalized = str(execution_class or "").strip().upper()
        if normalized == ExecutionClass.CONTROLLED_SIMULATOR.value:
            return self._simulator_connector
        raise ValueError(f"execution_class {execution_class} not supported by travel adapter")
