"""Shared adapter validation helpers."""

from __future__ import annotations

import re
from typing import Any, Mapping

from abis_grp_runtime.adapters.errors import AdapterValidationError

URL_PATTERN = re.compile(r"(?i)(https?://|file://|ftp://|\\\\)")


def reject_unknown_keys(data: Mapping[str, Any], allowed: frozenset[str]) -> None:
    unknown = sorted(set(data.keys()) - allowed)
    if unknown:
        raise AdapterValidationError("unsupported input fields", fields=unknown)


def require_fields(data: Mapping[str, Any], required: tuple[str, ...]) -> None:
    for field in required:
        if field not in data or data[field] in (None, ""):
            raise AdapterValidationError(f"missing required field: {field}", missing=field)


def reject_url_like_values(data: Mapping[str, Any]) -> None:
    for value in data.values():
        if isinstance(value, str) and URL_PATTERN.search(value):
            raise AdapterValidationError("URL-like input values are not permitted")
        if isinstance(value, Mapping):
            reject_url_like_values(value)


def reject_forbidden_keys(data: Mapping[str, Any], forbidden: frozenset[str]) -> None:
    for key in data.keys():
        lowered = str(key).lower()
        if lowered in forbidden:
            raise AdapterValidationError(f"forbidden field rejected: {key}", fields=[str(key)])
