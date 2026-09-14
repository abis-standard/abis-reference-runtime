"""M-206B external authenticated demo gateway (MOCK-ONLY)."""

from abis_grp_runtime.gateway.config import GatewayConfig
from abis_grp_runtime.gateway.errors import GatewayError, GatewayErrorCode
from abis_grp_runtime.gateway.server import gateway_public_base_url, start_external_gateway

__all__ = [
    "GatewayConfig",
    "GatewayError",
    "GatewayErrorCode",
    "gateway_public_base_url",
    "start_external_gateway",
]
