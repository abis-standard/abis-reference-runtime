"""Agent request/response envelopes — operational representations only."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from abis_grp_runtime.agent.errors import AgentErrorEnvelope


@dataclass(frozen=True)
class AgentIdentity:
    """Implementation participant/client identity — not normative ABIS Participant."""

    agent_id: str
    agent_type: str
    source: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
        }
        if self.source is not None:
            payload["source"] = self.source
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True)
class AgentRequestEnvelope:
    """
    Agent-neutral external entry request.

    Fields are operational/transport representations — not normative ABIS definitions.
    """

    agent_id: str
    operation: str
    execution_class: str
    authorization_token: str
    request_id: str | None = None
    correlation_id: str | None = None
    implementation_continuity_reference: str | None = None
    agent_type: str = "generic"
    structured_input: Mapping[str, Any] = field(default_factory=dict)
    constraints: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def identity(self) -> AgentIdentity:
        source = str(self.metadata.get("source")) if self.metadata.get("source") else None
        return AgentIdentity(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            source=source,
            metadata={"request_id": self.request_id} if self.request_id else {},
        )


@dataclass(frozen=True)
class AgentResponseEnvelope:
    """
    Agent-neutral external response.

    Keeps transport status, authorization, execution, Native Result, and Outcome distinct.
    """

    request_id: str
    correlation_id: str
    transport_status: str
    agent_identity: AgentIdentity
    authorization_disposition: dict[str, Any]
    execution_disposition: dict[str, Any]
    native_result: dict[str, Any] | None = None
    outcome_disposition: dict[str, Any] | None = None
    execution_provenance: dict[str, Any] | None = None
    trace_reference: dict[str, Any] = field(default_factory=dict)
    implementation_continuity_reference: str | None = None
    error: AgentErrorEnvelope | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "transport_status": self.transport_status,
            "agent_identity": self.agent_identity.to_dict(),
            "authorization_disposition": self.authorization_disposition,
            "execution_disposition": self.execution_disposition,
            "native_result": self.native_result,
            "outcome_disposition": self.outcome_disposition,
            "execution_provenance": self.execution_provenance,
            "trace_reference": self.trace_reference,
        }
        if self.implementation_continuity_reference is not None:
            payload["implementation_continuity_reference"] = self.implementation_continuity_reference
        if self.error is not None:
            payload["error"] = self.error.to_dict()
        return payload
