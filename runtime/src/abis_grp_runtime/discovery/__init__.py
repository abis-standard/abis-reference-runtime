"""Reference Runtime discovery — implementation-level, non-normative."""

from abis_grp_runtime.discovery.pointer import (
    POINTER_KIND,
    POINTER_VERSION,
    POINTER_WELL_KNOWN_PATH,
    build_reference_runtime_pointer,
    validate_pointer,
    validate_runtime_base_url,
)
from abis_grp_runtime.discovery.resolver import resolve_runtime_base_url

__all__ = [
    "POINTER_KIND",
    "POINTER_VERSION",
    "POINTER_WELL_KNOWN_PATH",
    "build_reference_runtime_pointer",
    "resolve_runtime_base_url",
    "validate_pointer",
    "validate_runtime_base_url",
]
