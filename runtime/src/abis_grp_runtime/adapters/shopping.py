"""Shopping Business Interaction Adapter."""

from __future__ import annotations

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
from abis_grp_runtime.connectors.commerce_simulator import CommerceSimulatorConnector
from abis_grp_runtime.descriptor.builder import build_descriptor

SHOPPING_ALLOWED_INPUT = frozenset(
    {
        "sku_id",
        "quantity",
        "idempotency_key",
        "test_scenario",
    }
)

SHOPPING_FORBIDDEN_INPUT = frozenset(
    {
        "card_number",
        "cvv",
        "pan",
        "payment_token",
        "payment_method",
        "stripe",
        "paypal",
        "email",
        "phone",
        "name",
        "address",
        "ssn",
        "customer_id",
        "callback_url",
        "webhook_url",
        "redirect_url",
    }
)

SHOPPING_STRUCTURED_INPUT_SPEC: dict[str, Any] = {
    "required_fields": ["sku_id", "quantity"],
    "optional_fields": ["idempotency_key", "test_scenario"],
    "field_types": {
        "sku_id": "string",
        "quantity": "integer",
        "idempotency_key": "string",
        "test_scenario": "string",
    },
}


class ShoppingBusinessAdapter(BusinessInteractionAdapter):
    adapter_id = "shopping"
    vertical = "shopping"
    supported_operations = frozenset({"submit_order"})
    default_execution_classes = frozenset({"CONTROLLED_SIMULATOR"})
    business_system_identifier = "abis-demo-commerce-simulator"

    def __init__(self, css_engine: Any) -> None:
        self._connector = CommerceSimulatorConnector(css_engine)

    def validate_structured_input(self, operation: str, structured_input: Mapping[str, Any]) -> None:
        if operation.strip().lower() != "submit_order":
            raise AdapterValidationError(f"unsupported operation: {operation}")
        if not isinstance(structured_input, dict):
            raise AdapterValidationError("structured_input must be an object")
        data = dict(structured_input)
        reject_forbidden_keys(data, SHOPPING_FORBIDDEN_INPUT)
        reject_unknown_keys(data, SHOPPING_ALLOWED_INPUT)
        reject_url_like_values(data)
        require_fields(data, ("sku_id", "quantity"))
        try:
            quantity = int(data["quantity"])
        except (TypeError, ValueError):
            raise AdapterValidationError("quantity must be an integer") from None
        if quantity <= 0:
            raise AdapterValidationError("quantity must be greater than zero")

    def get_descriptor(self, operation: str) -> dict[str, Any]:
        if operation.strip().lower() != "submit_order":
            raise AdapterValidationError(f"unsupported operation: {operation}")
        return build_descriptor(
            vertical=self.vertical,
            operation="submit_order",
            execution_classes_allowed=self.default_execution_classes,
            structured_input=SHOPPING_STRUCTURED_INPUT_SPEC,
            business_system_identifier=self.business_system_identifier,
            business_system_classification=self.business_system_classification,
        )

    def get_connector(self) -> BusinessConnectorPort:
        return self._connector
