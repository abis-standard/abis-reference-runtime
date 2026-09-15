"""External authenticated demo gateway (MOCK-ONLY)."""

from abis_grp_runtime.gateway.config import GatewayConfig
from abis_grp_runtime.gateway.errors import GatewayError, GatewayErrorCode
from abis_grp_runtime.gateway.reference_profile import (
    PROFILE_KIND,
    PROFILE_VERSION,
    REFERENCE_PROFILE_PATH,
    build_health_response,
    build_reference_runtime_profile,
)
from abis_grp_runtime.gateway.server import gateway_public_base_url, start_external_gateway

__all__ = [
    "GatewayConfig",
    "GatewayError",
    "GatewayErrorCode",
    "PROFILE_KIND",
    "PROFILE_VERSION",
    "REFERENCE_PROFILE_PATH",
    "build_health_response",
    "build_reference_runtime_profile",
    "gateway_public_base_url",
    "start_external_gateway",
]
