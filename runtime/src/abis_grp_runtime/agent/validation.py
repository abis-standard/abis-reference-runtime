"""Agent request validation — fail closed."""

from __future__ import annotations

from abis_grp_runtime.agent.envelope import AgentRequestEnvelope, SUPPORTED_OPERATIONS
from abis_grp_runtime.agent.errors import AgentContractErrorCode, AgentErrorEnvelope
from abis_grp_runtime.execution import ExecutionClass


def validate_agent_request(request: AgentRequestEnvelope) -> AgentErrorEnvelope | None:
    """Return error envelope if invalid; None if valid."""
    if not request.agent_id or not request.agent_id.strip():
        return AgentErrorEnvelope(
            code=AgentContractErrorCode.INVALID_REQUEST,
            message="agent_id is required",
        )
    if not request.operation or request.operation not in SUPPORTED_OPERATIONS:
        return AgentErrorEnvelope(
            code=AgentContractErrorCode.INVALID_REQUEST,
            message="unsupported or missing operation",
            detail={"supported": sorted(SUPPORTED_OPERATIONS)},
        )
    if not request.execution_class or not str(request.execution_class).strip():
        return AgentErrorEnvelope(
            code=AgentContractErrorCode.INVALID_REQUEST,
            message="execution_class is required",
        )
    if not request.authorization_token or not str(request.authorization_token).strip():
        return AgentErrorEnvelope(
            code=AgentContractErrorCode.INVALID_REQUEST,
            message="authorization_token is required",
        )
    parsed = ExecutionClass.parse(request.execution_class)
    if parsed is ExecutionClass.UNKNOWN and request.execution_class.upper() != "UNKNOWN":
        return AgentErrorEnvelope(
            code=AgentContractErrorCode.INVALID_REQUEST,
            message="invalid execution_class",
            detail={"execution_class": request.execution_class},
        )
    return None
