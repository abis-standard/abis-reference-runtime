"""Bearer authentication — constant-time comparison."""

from __future__ import annotations

import hmac


def extract_bearer_token(authorization_header: str | None) -> str | None:
    if not authorization_header:
        return None
    prefix = "Bearer "
    if not authorization_header.startswith(prefix):
        return None
    token = authorization_header[len(prefix) :].strip()
    return token or None


def verify_bearer(provided: str | None, expected: str) -> bool:
    if provided is None or not expected:
        return False
    return hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))
