"""ABIS Reference Runtime v0.1 — non-production reference implementation (MOCK-ONLY)."""

from abis_grp_runtime.agent import (
    AgentRequestEnvelope,
    AgentResponseEnvelope,
    ExternalAgentAdapter,
    serialize_request,
    serialize_response,
)
from abis_grp_runtime.connectors import RestaurantSimulatorConnector, SimulatorEgressFirewall
from abis_grp_runtime.core import RuntimeCore, RuntimePipelineResult
from abis_grp_runtime.context import RuntimeRequestContext
from abis_grp_runtime.e2e import GrokE2EResponse, GrokE2EService
from abis_grp_runtime.gateway import (
    GatewayConfig,
    GatewayError,
    GatewayErrorCode,
    gateway_public_base_url,
    start_external_gateway,
)
from abis_grp_runtime.native_result import NativeResultEnvelope

__all__ = [
    "AgentRequestEnvelope",
    "AgentResponseEnvelope",
    "ExternalAgentAdapter",
    "GatewayConfig",
    "GatewayError",
    "GatewayErrorCode",
    "GrokE2EResponse",
    "GrokE2EService",
    "NativeResultEnvelope",
    "RestaurantSimulatorConnector",
    "RuntimeCore",
    "RuntimePipelineResult",
    "RuntimeRequestContext",
    "SimulatorEgressFirewall",
    "gateway_public_base_url",
    "serialize_request",
    "serialize_response",
    "start_external_gateway",
]

__version__ = "0.1.0"
