"""External Agent contract — agent-neutral entry boundary (M-202)."""

from abis_grp_runtime.agent.adapter import ExternalAgentAdapter
from abis_grp_runtime.agent.envelope import (
    AgentIdentity,
    AgentRequestEnvelope,
    AgentResponseEnvelope,
    SUPPORTED_OPERATIONS,
)
from abis_grp_runtime.agent.errors import AgentContractErrorCode, AgentErrorEnvelope
from abis_grp_runtime.agent.serialization import (
    deserialize_request,
    deserialize_response,
    request_from_dict,
    request_to_dict,
    serialize_request,
    serialize_response,
)
from abis_grp_runtime.agent.validation import validate_agent_request

__all__ = [
    "AgentContractErrorCode",
    "AgentErrorEnvelope",
    "AgentIdentity",
    "AgentRequestEnvelope",
    "AgentResponseEnvelope",
    "ExternalAgentAdapter",
    "SUPPORTED_OPERATIONS",
    "deserialize_request",
    "deserialize_response",
    "request_from_dict",
    "request_to_dict",
    "serialize_request",
    "serialize_response",
    "validate_agent_request",
]
