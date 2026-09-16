"""Strict external request validation — fail closed, SSRF-safe, vertical-neutral."""

from __future__ import annotations

import re
from typing import Any, Mapping

from abis_grp_runtime.gateway.config import ALLOWED_EXECUTION_CLASSES
from abis_grp_runtime.adapters.errors import AdapterValidationError
from abis_grp_runtime.gateway.errors import GatewayError, GatewayErrorCode
from abis_grp_runtime.gateway.execution_surface import (
    is_advertised_invocation,
    published_operations,
    published_verticals,
)
from abis_grp_runtime.registry.interaction_registry import require_active_registry

DANGEROUS_TOP_LEVEL_KEYS = frozenset(
    {
        "url",
        "uri",
        "target",
        "target_url",
        "callback",
        "webhook",
        "proxy",
        "shell",
        "command",
        "cmd",
        "exec",
        "execute",
        "path",
        "file",
        "filepath",
        "script",
        "eval",
        "import",
        "pickle",
        "subprocess",
        "connector_target",
        "business_system_url",
    }
)

ALLOWED_TOP_LEVEL_KEYS = frozenset(
    {
        "agent_id",
        "agent_type",
        "operation",
        "execution_class",
        "authorization_token",
        "correlation_id",
        "request_id",
        "input",
        "structured_input",
        "metadata",
    }
)

URL_PATTERN = re.compile(r"(?i)(https?://|file://|ftp://|\\\\)")


def _contains_url_like(value: Any) -> bool:
    if isinstance(value, str) and URL_PATTERN.search(value):
        return True
    if isinstance(value, Mapping):
        return any(_contains_url_like(v) for v in value.values())
    if isinstance(value, list):
        return any(_contains_url_like(v) for v in value)
    return False


def _reject_unknown_keys(data: Mapping[str, Any], allowed: frozenset[str], label: str) -> GatewayError | None:
    unknown = sorted(set(data.keys()) - allowed)
    if unknown:
        return GatewayError(
            GatewayErrorCode.REQUEST_INVALID,
            f"unsupported {label} fields",
            http_status=400,
            detail={"fields": unknown},
        )
    return None


def validate_vertical(vertical: str | None) -> GatewayError | None:
    if not vertical:
        return GatewayError(GatewayErrorCode.REQUEST_INVALID, "vertical missing from route", http_status=404)
    normalized = vertical.strip().lower()
    allowed = published_verticals()
    if normalized not in allowed:
        return GatewayError(
            GatewayErrorCode.VERTICAL_DENIED,
            "vertical not enabled for reference execution surface",
            http_status=403,
            detail={"vertical": normalized, "allowed": sorted(allowed)},
        )
    return None


def validate_payload(data: Any, *, vertical: str) -> tuple[dict[str, Any] | None, GatewayError | None]:
    vertical_error = validate_vertical(vertical)
    if vertical_error:
        return None, vertical_error

    if not isinstance(data, dict):
        return None, GatewayError(GatewayErrorCode.REQUEST_INVALID, "JSON object required", http_status=400)

    for key in data.keys():
        lowered = str(key).lower()
        if lowered in DANGEROUS_TOP_LEVEL_KEYS:
            return None, GatewayError(
                GatewayErrorCode.REQUEST_INVALID,
                "dangerous field rejected",
                http_status=400,
                detail={"field": str(key)},
            )

    unknown_top = _reject_unknown_keys(data, ALLOWED_TOP_LEVEL_KEYS, "request")
    if unknown_top:
        return None, unknown_top

    if _contains_url_like(data):
        return None, GatewayError(
            GatewayErrorCode.REQUEST_INVALID,
            "URL-like values are not permitted",
            http_status=400,
        )

    required = ("agent_id", "agent_type", "operation", "execution_class", "correlation_id")
    missing = [k for k in required if not str(data.get(k) or "").strip()]
    if missing:
        return None, GatewayError(
            GatewayErrorCode.REQUEST_INVALID,
            "missing required fields",
            http_status=400,
            detail={"missing": missing},
        )

    operation = str(data["operation"]).strip().lower()
    allowed_ops = published_operations()
    if operation not in allowed_ops:
        return None, GatewayError(
            GatewayErrorCode.OPERATION_DENIED,
            "operation not allowed",
            http_status=403,
            detail={"operation": operation, "allowed": sorted(allowed_ops)},
        )

    execution_class = str(data["execution_class"]).strip().upper()
    if execution_class not in ALLOWED_EXECUTION_CLASSES:
        code = (
            GatewayErrorCode.EXECUTION_CLASS_DENIED
            if execution_class in ("REAL_EXTERNAL", "UNKNOWN")
            else GatewayErrorCode.REQUEST_INVALID
        )
        return None, GatewayError(
            code,
            "execution_class not allowed",
            http_status=403 if code is GatewayErrorCode.EXECUTION_CLASS_DENIED else 400,
            detail={"execution_class": execution_class, "allowed": sorted(ALLOWED_EXECUTION_CLASSES)},
        )

    if not is_advertised_invocation(vertical, operation, execution_class):
        if operation not in allowed_ops:
            return None, GatewayError(
                GatewayErrorCode.OPERATION_DENIED,
                "operation not allowed",
                http_status=403,
                detail={"operation": operation, "allowed": sorted(allowed_ops)},
            )
        return None, GatewayError(
            GatewayErrorCode.EXECUTION_CLASS_DENIED,
            "execution_class not allowed",
            http_status=403,
            detail={"execution_class": execution_class, "allowed": sorted(ALLOWED_EXECUTION_CLASSES)},
        )

    input_key = "structured_input" if "structured_input" in data else "input"
    if input_key not in data or not isinstance(data[input_key], dict):
        return None, GatewayError(
            GatewayErrorCode.REQUEST_INVALID,
            "input object required",
            http_status=400,
        )

    structured = dict(data[input_key])
    if _contains_url_like(structured):
        return None, GatewayError(
            GatewayErrorCode.REQUEST_INVALID,
            "URL-like input values are not permitted",
            http_status=400,
        )

    registry = require_active_registry()
    try:
        registry.validate_structured_input(vertical, operation, structured)
    except AdapterValidationError as exc:
        return None, GatewayError(
            GatewayErrorCode.REQUEST_INVALID,
            str(exc),
            http_status=400,
            detail={"missing": exc.missing, "fields": exc.fields} if exc.missing or exc.fields else None,
        )

    normalized = dict(data)
    normalized["structured_input"] = structured
    normalized.pop("input", None)
    normalized["vertical"] = vertical.strip().lower()
    if "authorization_token" not in normalized or not str(normalized.get("authorization_token") or "").strip():
        normalized["authorization_token"] = "ALLOW"
    return normalized, None
