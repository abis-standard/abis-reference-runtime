"""External Agent contract — agent-neutral entry boundary (M-202)."""

from abis_grp_runtime.agent.adapter import ExternalAgentAdapter
from abis_grp_runtime.agent.envelope import (
    AgentIdentity,
    AgentRequestEnvelope,
    AgentResponseEnvelope,
    SUPPORTED_OPERATIONS,
)
from abis_grp_runtime.agent.errors import AgentContractErrorCode, AgentErrorEnvelope
from abis_grp_runtime.discovery import (
    POINTER_KIND,
    POINTER_WELL_KNOWN_PATH,
    build_reference_runtime_pointer,
    resolve_runtime_base_url,
    validate_pointer,
    validate_runtime_base_url,
)
from abis_grp_runtime.agent.reference_client import (
    ReferenceAgentClient,
    ReferenceClientConfig,
    ReferenceClientError,
    ReferenceClientResult,
    gateway_token_from_env,
)
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
    "POINTER_KIND",
    "POINTER_WELL_KNOWN_PATH",
    "AgentContractErrorCode",
    "AgentErrorEnvelope",
    "AgentIdentity",
    "AgentRequestEnvelope",
    "AgentResponseEnvelope",
    "ExternalAgentAdapter",
    "ReferenceAgentClient",
    "ReferenceClientConfig",
    "ReferenceClientError",
    "ReferenceClientResult",
    "SUPPORTED_OPERATIONS",
    "deserialize_request",
    "deserialize_response",
    "gateway_token_from_env",
    "request_from_dict",
    "request_to_dict",
    "serialize_request",
    "serialize_response",
    "validate_agent_request",
    "validate_pointer",
    "validate_runtime_base_url",
    "build_reference_runtime_pointer",
    "resolve_runtime_base_url",
]
