"""Interaction preflight — read-only profile compatibility check before invocation."""

from __future__ import annotations

import re
from typing import Any

from abis_grp_runtime.gateway.config import GatewayConfig
from abis_grp_runtime.gateway.execution_surface import EXECUTION_SURFACE_REVISION, find_advertised_interaction
from abis_grp_runtime.gateway.reference_profile import PROFILE_VERSION
from abis_grp_runtime.version import __version__ as RUNTIME_VERSION

PREFLIGHT_READY = "PREFLIGHT_READY"
PREFLIGHT_NOT_ADVERTISED = "PREFLIGHT_NOT_ADVERTISED"
PREFLIGHT_EXECUTION_DENIED = "PREFLIGHT_EXECUTION_DENIED"
PREFLIGHT_INVALID_REQUEST = "PREFLIGHT_INVALID_REQUEST"

ALLOWED_PREFLIGHT_KEYS = frozenset({"operation", "execution_class", "correlation_id"})

URL_PATTERN = re.compile(r"(?i)(https?://|file://|ftp://|\\\\)")

PREFLIGHT_DISCLAIMER = {
    "business_outcome_prediction": False,
    "conformance_determination": False,
    "certification": False,
}


def _invalid_response(
    *,
    vertical: str,
    operation: str | None = None,
    execution_class: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "preflight_state": PREFLIGHT_INVALID_REQUEST,
        "vertical": vertical,
        "disclaimer": dict(PREFLIGHT_DISCLAIMER),
    }
    if operation is not None:
        body["operation"] = operation
    if execution_class is not None:
        body["execution_class"] = execution_class
    return body


def parse_preflight_payload(data: Any, *, vertical: str) -> tuple[dict[str, str] | None, dict[str, Any] | None]:
    """Return (parsed fields, invalid preflight response) — one will be None."""
    vertical_norm = vertical.strip().lower()
    if not isinstance(data, dict):
        return None, _invalid_response(vertical=vertical_norm)

    unknown = sorted(set(data.keys()) - ALLOWED_PREFLIGHT_KEYS)
    if unknown:
        return None, _invalid_response(vertical=vertical_norm)

    for value in data.values():
        if isinstance(value, str) and URL_PATTERN.search(value):
            return None, _invalid_response(vertical=vertical_norm)

    operation_raw = data.get("operation")
    execution_raw = data.get("execution_class")
    if operation_raw is None or not str(operation_raw).strip():
        return None, _invalid_response(vertical=vertical_norm, execution_class=_normalize_execution(execution_raw))
    if execution_raw is None or not str(execution_raw).strip():
        return None, _invalid_response(
            vertical=vertical_norm,
            operation=str(operation_raw).strip().lower(),
        )

    parsed: dict[str, str] = {
        "operation": str(operation_raw).strip().lower(),
        "execution_class": str(execution_raw).strip().upper(),
    }
    correlation_raw = data.get("correlation_id")
    if correlation_raw is not None:
        correlation = str(correlation_raw).strip()
        if not correlation:
            return None, _invalid_response(vertical=vertical_norm)
        parsed["correlation_id"] = correlation
    return parsed, None


def _normalize_execution(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().upper()
    return text or None


def _evidence_metadata(correlation_id: str | None = None) -> dict[str, Any]:
    """Implementation-level preflight evidence — not normative ABIS semantics."""
    evidence: dict[str, Any] = {
        "runtime_version": RUNTIME_VERSION,
        "profile_version": PROFILE_VERSION,
        "execution_surface_revision": EXECUTION_SURFACE_REVISION,
    }
    if correlation_id:
        evidence["correlation_id"] = correlation_id
    return evidence


def evaluate_preflight(
    config: GatewayConfig,
    *,
    vertical: str,
    operation: str,
    execution_class: str,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Evaluate against canonical reference execution surface."""
    _ = config  # reserved for future mode/bind-specific preflight fields
    vertical_norm = vertical.strip().lower()
    evidence = _evidence_metadata(correlation_id)
    matched = find_advertised_interaction(vertical_norm, operation)

    if matched is None:
        return {
            "preflight_state": PREFLIGHT_NOT_ADVERTISED,
            "vertical": vertical_norm,
            "operation": operation,
            "execution_class": execution_class,
            "disclaimer": dict(PREFLIGHT_DISCLAIMER),
            "evidence": evidence,
        }

    if execution_class not in matched.execution_classes_allowed:
        return {
            "preflight_state": PREFLIGHT_EXECUTION_DENIED,
            "vertical": vertical_norm,
            "operation": operation,
            "execution_class": execution_class,
            "disclaimer": dict(PREFLIGHT_DISCLAIMER),
            "evidence": evidence,
        }

    return {
        "preflight_state": PREFLIGHT_READY,
        "vertical": vertical_norm,
        "operation": operation,
        "execution_class": execution_class,
        "invocation": matched.to_dict()["invocation"],
        "disclaimer": dict(PREFLIGHT_DISCLAIMER),
        "evidence": evidence,
    }
