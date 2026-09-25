"""Reference runtime E2E integration service — multi-vertical, no outcome evaluation."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from abis_grp_runtime.agent.adapter import ExternalAgentAdapter
from abis_grp_runtime.agent.envelope import AgentRequestEnvelope, AgentResponseEnvelope
from abis_grp_runtime.agent.execution_provenance import build_execution_provenance, merge_connector_provenance
from abis_grp_runtime.connectors.authorized_http_sandbox import AuthorizedHttpSandboxConnector
from abis_grp_runtime.execution import ExecutionClass
from abis_grp_runtime.agent.serialization import request_from_dict
from abis_grp_runtime.core import RuntimeCore
from abis_grp_runtime.registry.interaction_registry import RuntimeInteractionRegistry


class GrokE2EService:
    """
    LEGACY_INTERNAL_NAME: GrokE2EService
    PUBLIC_SEMANTICS: provider-neutral reference runtime integration service.

    Routes Agent Contract → Runtime Core → Adapter Connector → controlled simulator.
    Does not perform normative ABIS Business Outcome evaluation.
    """

    def __init__(self, registry: RuntimeInteractionRegistry) -> None:
        self._registry = registry

    @property
    def registry(self) -> RuntimeInteractionRegistry:
        return self._registry

    def invoke(self, request: AgentRequestEnvelope) -> AgentResponseEnvelope:
        vertical = str(request.metadata.get("vertical") or "").strip().lower()
        if not vertical:
            raise ValueError("vertical missing from request metadata")
        operation = request.operation.strip().lower()
        adapter = self._registry.get_adapter(vertical, operation)
        registered = self._registry.find(vertical, operation)
        execution_class = ExecutionClass.parse(request.execution_class)
        try:
            connector = adapter.get_connector_for_execution_class(execution_class.value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        bound_operation = adapter.bind_operation(operation)
        runtime = RuntimeCore(connector=connector)
        adapter_client = ExternalAgentAdapter(runtime)
        icr = request.implementation_continuity_reference
        provenance = build_execution_provenance(
            vertical=vertical,
            operation=operation,
            business_system_identifier=adapter.business_system_identifier,
            business_system_classification=adapter.business_system_classification,
            descriptor_path=registered.descriptor_path if registered else None,
            implementation_continuity_reference=icr,
        )
        response = adapter_client.invoke(request, execution_provenance=provenance)
        if isinstance(connector, AuthorizedHttpSandboxConnector):
            response = replace(
                response,
                execution_provenance=merge_connector_provenance(
                    response.execution_provenance,
                    connector.consume_execution_metadata(),
                ),
            )
        return response

    def invoke_from_dict(self, payload: Mapping[str, Any]) -> AgentResponseEnvelope:
        data = dict(payload)
        if "structured_input" not in data and "input" in data:
            data["structured_input"] = dict(data.pop("input"))
        if data.get("implementation_continuity_reference") is not None:
            data["implementation_continuity_reference"] = str(
                data["implementation_continuity_reference"]
            ).strip() or None
        if "authorization_token" not in data:
            data["authorization_token"] = "ALLOW"
        if "execution_class" not in data:
            data["execution_class"] = "CONTROLLED_SIMULATOR"
        vertical = str(data.get("vertical") or "").strip().lower()
        if not vertical:
            raise ValueError("vertical missing from invoke payload")
        metadata = dict(data.get("metadata") or {})
        metadata["vertical"] = vertical
        data["metadata"] = metadata
        request = request_from_dict(data)
        return self.invoke(request)
