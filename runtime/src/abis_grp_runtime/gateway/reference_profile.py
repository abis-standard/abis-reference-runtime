"""Reference Runtime Profile — implementation surface advertisement, not normative ABIS semantics."""

from __future__ import annotations

from typing import Any

from abis_grp_runtime.version import __version__ as RUNTIME_VERSION
from abis_grp_runtime.gateway.config import GatewayConfig
from abis_grp_runtime.gateway.execution_surface import (
    EXECUTION_SURFACE_REVISION,
    advertised_interactions,
)
from abis_grp_runtime.registry.interaction_registry import require_active_registry

PROFILE_KIND = "abis-reference-runtime-profile"
PROFILE_VERSION = 4
RUNTIME_NAME = "abis-reference-runtime"
REFERENCE_PROFILE_PATH = "/v1/reference-profile"
HEALTH_PATH = "/health"
DESCRIPTOR_PATH_PREFIX = "/v1/reference-profile/interactions"

FUTURE_VERTICALS_RESERVED = ("dental", "government", "travel")


def build_reference_runtime_profile(config: GatewayConfig) -> dict[str, Any]:
    """Canonical machine-readable description of the public execution surface."""
    _ = config
    interactions = advertised_interactions()
    return {
        "profile_kind": PROFILE_KIND,
        "profile_version": PROFILE_VERSION,
        "runtime": {
            "name": RUNTIME_NAME,
            "version": RUNTIME_VERSION,
            "implementation_language": "python",
        },
        "authority": {
            "semantic": "NONE",
            "normative": "NONE",
        },
        "execution_surface_revision": EXECUTION_SURFACE_REVISION,
        "advertised_interactions": interactions,
        "authorization": {
            "invoke": {
                "required": True,
                "scheme": "bearer",
            },
        },
        "execution_boundary": {
            "real_execution": "PROHIBITED",
        },
        "outcome_boundary": {
            "normative_business_outcome_evaluation": "NOT_IMPLEMENTED",
            "completion_determination": "NOT_IMPLEMENTED",
        },
        "implementation_continuity": {
            "field": "implementation_continuity_reference",
            "semantic_authority": "NONE",
            "disclaimer": "implementation correlation only — not ABIS Interaction identity",
        },
        "technical_observation": {
            "restaurant": {
                "method": "POST",
                "path": "/v1/demo/restaurant/observe",
                "purpose": "native technical observation only",
                "business_outcome_evaluation": "NOT_IMPLEMENTED",
            },
        },
        "health": {
            "method": "GET",
            "path": HEALTH_PATH,
        },
    }


def build_health_response(config: GatewayConfig) -> dict[str, Any]:
    """Lightweight health payload — overlapping fields sourced from the profile builder."""
    profile = build_reference_runtime_profile(config)
    verticals = sorted({item["vertical"] for item in profile["advertised_interactions"]})
    operations = sorted({item["operation"] for item in profile["advertised_interactions"]})
    execution_classes = sorted(
        {
            execution_class
            for item in profile["advertised_interactions"]
            for execution_class in item["execution_classes_allowed"]
        }
    )
    return {
        "ok": True,
        "service": "abis-external-demo-gateway",
        "mode": config.mode,
        "bind": config.host,
        "verticals_enabled": verticals,
        "future_verticals_reserved": list(FUTURE_VERTICALS_RESERVED),
        "operations_allowed": operations,
        "execution_class_allowed": execution_classes,
        "real_execution": profile["execution_boundary"]["real_execution"],
        "reference_runtime": f"v{profile['runtime']['version']}",
        "semantic_authority": profile["authority"]["semantic"],
    }
