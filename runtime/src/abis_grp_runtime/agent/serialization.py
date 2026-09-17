"""Agent-neutral JSON serialization contract."""

from __future__ import annotations

import json
from typing import Any, Mapping

from abis_grp_runtime.agent.envelope import AgentRequestEnvelope, AgentResponseEnvelope


def request_to_dict(request: AgentRequestEnvelope) -> dict[str, Any]:
    return {
        "request_id": request.request_id,
        "correlation_id": request.correlation_id,
        "implementation_continuity_reference": request.implementation_continuity_reference,
        "agent_id": request.agent_id,
        "agent_type": request.agent_type,
        "operation": request.operation,
        "structured_input": dict(request.structured_input),
        "constraints": dict(request.constraints),
        "execution_class": request.execution_class,
        "authorization_token": request.authorization_token,
        "metadata": dict(request.metadata),
    }


def request_from_dict(data: Mapping[str, Any]) -> AgentRequestEnvelope:
    return AgentRequestEnvelope(
        request_id=data.get("request_id"),
        correlation_id=data.get("correlation_id"),
        implementation_continuity_reference=data.get("implementation_continuity_reference"),
        agent_id=str(data.get("agent_id", "")),
        agent_type=str(data.get("agent_type", "generic")),
        operation=str(data.get("operation", "")),
        structured_input=dict(data.get("structured_input") or {}),
        constraints=dict(data.get("constraints") or {}),
        execution_class=str(data.get("execution_class", "")),
        authorization_token=str(data.get("authorization_token", "")),
        metadata=dict(data.get("metadata") or {}),
    )


def serialize_request(request: AgentRequestEnvelope) -> str:
    return json.dumps(request_to_dict(request), sort_keys=True)


def deserialize_request(payload: str | Mapping[str, Any]) -> AgentRequestEnvelope:
    if isinstance(payload, str):
        data = json.loads(payload)
    else:
        data = payload
    return request_from_dict(data)


def serialize_response(response: AgentResponseEnvelope) -> str:
    return json.dumps(response.to_dict(), sort_keys=True)


def deserialize_response(payload: str | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(payload, str):
        return json.loads(payload)
    return dict(payload)
