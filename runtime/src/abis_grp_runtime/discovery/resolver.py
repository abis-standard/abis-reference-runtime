"""Business-origin Runtime Pointer resolution — untrusted input, fail closed."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from abis_grp_runtime.discovery.pointer import (
    POINTER_WELL_KNOWN_PATH,
    PointerValidationError,
    extract_runtime_base_url,
    validate_pointer,
)

_USERINFO_PATTERN = re.compile(r"^[^/@]+@[^/@]+")


class DiscoveryError(Exception):
    """Fail-closed business-origin discovery error."""


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise HTTPError(req.full_url, code, msg, headers, fp)


def validate_business_origin(origin: str) -> str:
    """Validate business origin URL — http/https only, no userinfo."""
    text = str(origin or "").strip()
    if not text:
        raise DiscoveryError("business origin missing")
    parsed = urlparse(text)
    if parsed.scheme not in ("http", "https"):
        raise DiscoveryError("business origin must use http or https")
    if not parsed.netloc:
        raise DiscoveryError("business origin missing host")
    if parsed.username or parsed.password or _USERINFO_PATTERN.search(parsed.netloc):
        raise DiscoveryError("business origin userinfo rejected")
    if parsed.fragment:
        raise DiscoveryError("business origin fragment rejected")
    if parsed.query:
        raise DiscoveryError("business origin query rejected")
    path = parsed.path or ""
    if ".." in path:
        raise DiscoveryError("business origin path traversal rejected")
    return f"{parsed.scheme}://{parsed.netloc}{path}".rstrip("/")


def pointer_url_for_origin(business_origin: str) -> str:
    origin = validate_business_origin(business_origin)
    return f"{origin}{POINTER_WELL_KNOWN_PATH}"


def resolve_runtime_base_url(business_origin: str, *, timeout: float = 10.0) -> tuple[dict[str, Any], str]:
    """
    Fetch and validate a Reference Runtime Pointer from a known Business Origin.

    Credentials are never attached to the discovery request.
    """
    url = pointer_url_for_origin(business_origin)
    request = Request(url, method="GET")
    opener = build_opener(_NoRedirectHandler())
    try:
        with opener.open(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise DiscoveryError(f"pointer fetch failed: HTTP {exc.code}") from exc
    except json.JSONDecodeError as exc:
        raise DiscoveryError("pointer response is not valid JSON") from exc
    except OSError as exc:
        raise DiscoveryError(f"pointer fetch failed: {exc}") from exc

    try:
        pointer = validate_pointer(body)
        base_url = extract_runtime_base_url(pointer)
    except PointerValidationError as exc:
        raise DiscoveryError(str(exc)) from exc
    return pointer, base_url
