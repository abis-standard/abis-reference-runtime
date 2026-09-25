"""Restaurant Business Interaction Adapter."""

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
from abis_grp_runtime.adapters.http_adapter_config import (
    RestaurantHttpAdapterConfig,
    load_restaurant_http_adapter_config_from_env,
)
from abis_grp_runtime.connectors.authorized_http_sandbox import AuthorizedHttpSandboxConnector
from abis_grp_runtime.connectors.restaurant_simulator import RestaurantSimulatorConnector
from abis_grp_runtime.execution import ExecutionClass
from abis_grp_runtime.descriptor.builder import build_descriptor

RESTAURANT_ALLOWED_INPUT = frozenset(
    {
        "date",
        "time",
        "party_size",
        "seating_type",
        "customer_reference",
        "test_scenario",
        "idempotency_key",
        "_test_reason_override",
        "_test_scenario_override",
    }
)

RESTAURANT_STRUCTURED_INPUT_SPEC: dict[str, Any] = {
    "required_fields": ["date", "time", "party_size", "seating_type"],
    "optional_fields": ["customer_reference", "idempotency_key", "test_scenario"],
    "field_types": {
        "date": "string",
        "time": "string",
        "party_size": "integer",
        "seating_type": "string",
        "customer_reference": "string",
        "idempotency_key": "string",
        "test_scenario": "string",
    },
}


class RestaurantBusinessAdapter(BusinessInteractionAdapter):
    adapter_id = "restaurant"
    vertical = "restaurant"
    supported_operations = frozenset({"reserve"})
    default_execution_classes = frozenset({"CONTROLLED_SIMULATOR", "AUTHORIZED_NON_PRODUCTION"})
    business_system_identifier = "abis-demo-restaurant-simulator"

    def __init__(
        self,
        crs_engine: Any,
        *,
        http_adapter_config: RestaurantHttpAdapterConfig | None = None,
    ) -> None:
        self._simulator_connector = RestaurantSimulatorConnector(crs_engine)
        self._http_config = http_adapter_config
        if self._http_config is None:
            self._http_config = load_restaurant_http_adapter_config_from_env()
        self._http_connector: AuthorizedHttpSandboxConnector | None = None
        if self._http_config and self._http_config.structurally_valid():
            self._http_connector = AuthorizedHttpSandboxConnector(self._http_config)

    @property
    def http_adapter_config(self) -> RestaurantHttpAdapterConfig | None:
        return self._http_config

    def http_adapter_configured(self) -> bool:
        return self._http_connector is not None

    def validate_structured_input(self, operation: str, structured_input: Mapping[str, Any]) -> None:
        if operation.strip().lower() != "reserve":
            raise AdapterValidationError(f"unsupported operation: {operation}")
        if not isinstance(structured_input, dict):
            raise AdapterValidationError("structured_input must be an object")
        data = dict(structured_input)
        reject_unknown_keys(data, RESTAURANT_ALLOWED_INPUT)
        reject_url_like_values(data)
        require_fields(data, ("date", "time", "party_size", "seating_type"))
        try:
            int(data["party_size"])
        except (TypeError, ValueError):
            raise AdapterValidationError("party_size must be an integer") from None

    def get_descriptor(self, operation: str) -> dict[str, Any]:
        if operation.strip().lower() != "reserve":
            raise AdapterValidationError(f"unsupported operation: {operation}")
        return build_descriptor(
            vertical=self.vertical,
            operation="reserve",
            execution_classes_allowed=self.default_execution_classes,
            structured_input=RESTAURANT_STRUCTURED_INPUT_SPEC,
            business_system_identifier=self.business_system_identifier,
            business_system_classification=self.business_system_classification,
        )

    def get_connector(self) -> BusinessConnectorPort:
        return self._simulator_connector

    def get_connector_for_execution_class(self, execution_class: str) -> BusinessConnectorPort:
        normalized = str(execution_class or "").strip().upper()
        if normalized == ExecutionClass.CONTROLLED_SIMULATOR.value:
            return self._simulator_connector
        if normalized == ExecutionClass.AUTHORIZED_NON_PRODUCTION.value:
            if self._http_connector is None:
                raise ValueError("AUTHORIZED_NON_PRODUCTION adapter not configured")
            return self._http_connector
        raise ValueError(f"execution_class {execution_class} not supported by restaurant adapter")
