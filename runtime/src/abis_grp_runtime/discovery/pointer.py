"""Reference Runtime Pointer — implementation-level business→runtime locator."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping
from urllib.parse import urlparse

POINTER_KIND = "abis-reference-runtime-pointer"
POINTER_VERSION = 1
POINTER_WELL_KNOWN_PATH = "/.well-known/abis-reference-runtime"
SUPPORTED_POINTER_VERSIONS = frozenset({POINTER_VERSION})

FORBIDDEN_POINTER_TERMS = (
    "ABIS Capability Manifest",
    "Capability Manifest",
    "ABIS Compatible",
    "ABIS Conformant",
    "ABIS Certified",
    "ABIS Discovery Standard",
    "ABIS Business Manifest",
    "ABIS Conformance Manifest",
    "ABIS Compatibility Manifest",
    "/.well-known/abis",
)

_USERINFO_PATTERN = re.compile(r"^[^/@]+@[^/@]+")


class PointerValidationError(ValueError):
    """Fail-closed pointer validation error."""


def build_reference_runtime_pointer(runtime_base_url: str) -> dict[str, Any]:
    """Build a reference-only Runtime Pointer document."""
    base_url = validate_runtime_base_url(runtime_base_url)
    return {
        "pointer_kind": POINTER_KIND,
        "pointer_version": POINTER_VERSION,
        "authority": {
            "semantic": "NONE",
            "normative": "NONE",
        },
        "runtime": {
            "base_url": base_url,
        },
    }


def validate_runtime_base_url(url: str) -> str:
    """Validate and normalize a Runtime base URL — http/https only, no userinfo."""
    text = str(url or "").strip()
    if not text:
        raise PointerValidationError("runtime base_url missing")
    parsed = urlparse(text)
    if parsed.scheme not in ("http", "https"):
        raise PointerValidationError("runtime base_url must use http or https")
    if not parsed.netloc:
        raise PointerValidationError("runtime base_url missing host")
    if parsed.username or parsed.password or _USERINFO_PATTERN.search(parsed.netloc):
        raise PointerValidationError("runtime base_url userinfo rejected")
    if parsed.fragment:
        raise PointerValidationError("runtime base_url fragment rejected")
    if ".." in parsed.path:
        raise PointerValidationError("runtime base_url path traversal rejected")
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path or ''}".rstrip("/")
    return normalized


def validate_pointer(data: Any) -> dict[str, Any]:
    """Validate a parsed Runtime Pointer document."""
    if not isinstance(data, dict):
        raise PointerValidationError("pointer must be a JSON object")
    serialized = json.dumps(data)
    for term in FORBIDDEN_POINTER_TERMS:
        if term in serialized:
            raise PointerValidationError(f"forbidden pointer term: {term}")
    if data.get("pointer_kind") != POINTER_KIND:
        raise PointerValidationError("invalid pointer_kind")
    version = data.get("pointer_version")
    if version not in SUPPORTED_POINTER_VERSIONS:
        raise PointerValidationError("unsupported pointer_version")
    authority = data.get("authority")
    if not isinstance(authority, dict):
        raise PointerValidationError("invalid authority")
    if authority.get("semantic") != "NONE" or authority.get("normative") != "NONE":
        raise PointerValidationError("pointer authority must be NONE")
    runtime = data.get("runtime")
    if not isinstance(runtime, dict):
        raise PointerValidationError("invalid runtime block")
    base_url = runtime.get("base_url")
    if not isinstance(base_url, str) or not base_url.strip():
        raise PointerValidationError("runtime base_url missing")
    validate_runtime_base_url(base_url)
    return dict(data)


def extract_runtime_base_url(pointer: Mapping[str, Any]) -> str:
    """Return normalized Runtime base URL from a validated pointer."""
    validated = validate_pointer(pointer)
    runtime = validated["runtime"]
    assert isinstance(runtime, dict)
    return validate_runtime_base_url(str(runtime["base_url"]))
