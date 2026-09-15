"""External authenticated demo gateway (MOCK-ONLY)."""

from abis_grp_runtime.gateway.config import GatewayConfig
from abis_grp_runtime.gateway.errors import GatewayError, GatewayErrorCode
from abis_grp_runtime.gateway.preflight import (
    PREFLIGHT_EXECUTION_DENIED,
    PREFLIGHT_INVALID_REQUEST,
    PREFLIGHT_NOT_ADVERTISED,
    PREFLIGHT_READY,
    evaluate_preflight,
    parse_preflight_payload,
)
from abis_grp_runtime.gateway.execution_surface import (
    advertised_interactions,
    find_advertised_interaction,
    is_advertised_invocation,
    reference_execution_surface,
)
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
    "PREFLIGHT_EXECUTION_DENIED",
    "PREFLIGHT_INVALID_REQUEST",
    "PREFLIGHT_NOT_ADVERTISED",
    "PREFLIGHT_READY",
    "PROFILE_KIND",
    "PROFILE_VERSION",
    "REFERENCE_PROFILE_PATH",
    "advertised_interactions",
    "build_health_response",
    "build_reference_runtime_profile",
    "evaluate_preflight",
    "find_advertised_interaction",
    "gateway_public_base_url",
    "is_advertised_invocation",
    "parse_preflight_payload",
    "reference_execution_surface",
    "start_external_gateway",
]
