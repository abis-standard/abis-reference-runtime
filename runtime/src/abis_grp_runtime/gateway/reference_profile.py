"""Reference Runtime Profile — implementation surface advertisement, not normative ABIS semantics."""

from __future__ import annotations

from typing import Any

from abis_grp_runtime.version import __version__ as RUNTIME_VERSION
from abis_grp_runtime.gateway.config import (
    ALLOWED_EXECUTION_CLASSES,
    ALLOWED_OPERATIONS,
    ALLOWED_VERTICALS_M206B,
    GatewayConfig,
)

PROFILE_KIND = "abis-reference-runtime-profile"
PROFILE_VERSION = 1
RUNTIME_NAME = "abis-reference-runtime"
REFERENCE_PROFILE_PATH = "/v1/reference-profile"
HEALTH_PATH = "/health"

BUSINESS_SYSTEM_IDENTIFIER = "abis-demo-restaurant-simulator"
BUSINESS_SYSTEM_CLASSIFICATION = "EXTERNAL_BUSINESS_SYSTEM_TEST_DOUBLE"

FUTURE_VERTICALS_RESERVED = ("shopping", "dental", "government", "travel")


def advertised_interactions() -> list[dict[str, Any]]:
    """Public gateway truth — only externally invokable vertical/operation pairs."""
    interactions: list[dict[str, Any]] = []
    for vertical in sorted(ALLOWED_VERTICALS_M206B):
        for operation in sorted(ALLOWED_OPERATIONS):
            interactions.append(
                {
                    "vertical": vertical,
                    "operation": operation,
                    "execution_classes_allowed": sorted(ALLOWED_EXECUTION_CLASSES),
                    "invocation": {
                        "method": "POST",
                        "path": f"/v1/demo/{vertical}/invoke",
                    },
                }
            )
    return interactions


def build_reference_runtime_profile(config: GatewayConfig) -> dict[str, Any]:
    """Canonical machine-readable description of the public execution surface."""
    _ = config  # reserved for future mode/bind-specific profile fields
    return {
        "profile_kind": PROFILE_KIND,
        "profile_version": PROFILE_VERSION,
        "runtime": {
            "name": RUNTIME_NAME,
            "version": RUNTIME_VERSION,
        },
        "authority": {
            "semantic": "NONE",
            "normative": "NONE",
        },
        "business_system": {
            "identifier": BUSINESS_SYSTEM_IDENTIFIER,
            "classification": BUSINESS_SYSTEM_CLASSIFICATION,
        },
        "advertised_interactions": advertised_interactions(),
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
