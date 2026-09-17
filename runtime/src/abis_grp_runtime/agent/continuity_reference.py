"""Implementation Continuity Reference — non-normative implementation correlation only."""

from __future__ import annotations

import re
import uuid

ICR_MAX_LENGTH = 128
ICR_FIELD_NAME = "implementation_continuity_reference"

_SECRET_PATTERNS = (
    re.compile(r"(?i)\bbearer\s+"),
    re.compile(r"(?i)\bauthorization\s*[:=]"),
    re.compile(r"https?://[^\s/]+@[^\s/]+"),
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]"),
    re.compile(r"(?i)eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]+\."),  # JWT-like
)


def generate_icr() -> str:
    """Generate opaque UUID v4 implementation continuity reference."""
    return str(uuid.uuid4())


def validate_icr(
    value: str | None,
    *,
    forbidden_equals: tuple[str | None, ...] = (),
) -> str | None:
    """
    Return error message if invalid; None if valid.

    Empty/None is valid — caller decides whether generation is required.
    """
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return f"{ICR_FIELD_NAME} must be non-empty when supplied"
    if len(normalized) > ICR_MAX_LENGTH:
        return f"{ICR_FIELD_NAME} exceeds max length {ICR_MAX_LENGTH}"
    for pattern in _SECRET_PATTERNS:
        if pattern.search(normalized):
            return f"{ICR_FIELD_NAME} contains disallowed secret-like material"
    for forbidden in forbidden_equals:
        if forbidden is not None and normalized == str(forbidden).strip():
            return f"{ICR_FIELD_NAME} must not equal other correlation identifiers"
    return None
