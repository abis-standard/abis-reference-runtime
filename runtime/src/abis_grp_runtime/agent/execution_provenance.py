"""Execution provenance — implementation-level invoke metadata (non-normative)."""

from __future__ import annotations

from typing import Any

from abis_grp_runtime.descriptor.constants import DESCRIPTOR_VERSION, descriptor_path_for


def build_execution_provenance(
    *,
    vertical: str,
    operation: str,
    business_system_identifier: str,
    business_system_classification: str = "EXTERNAL_BUSINESS_SYSTEM_TEST_DOUBLE",
    descriptor_path: str | None = None,
    implementation_continuity_reference: str | None = None,
    observation_kind: str | None = None,
) -> dict[str, Any]:
    """Build minimal vertical-neutral execution provenance for Invoke responses."""
    from abis_grp_runtime.gateway.execution_surface import EXECUTION_SURFACE_REVISION
    from abis_grp_runtime.gateway.reference_profile import PROFILE_VERSION, RUNTIME_NAME
    from abis_grp_runtime.version import __version__ as RUNTIME_VERSION

    vertical_norm = vertical.strip().lower()
    operation_norm = operation.strip().lower()
    result: dict[str, Any] = {
        "runtime": {
            "name": RUNTIME_NAME,
            "version": RUNTIME_VERSION,
        },
        "profile_version": PROFILE_VERSION,
        "execution_surface_revision": EXECUTION_SURFACE_REVISION,
        "interaction": {
            "vertical": vertical_norm,
            "operation": operation_norm,
        },
        "descriptor_path": descriptor_path or descriptor_path_for(vertical_norm, operation_norm),
        "descriptor_version": DESCRIPTOR_VERSION,
        "business_system": {
            "identifier": business_system_identifier,
            "classification": business_system_classification,
        },
    }
    if implementation_continuity_reference:
        result["implementation_continuity_reference"] = implementation_continuity_reference
        result["implementation_continuity_disclaimer"] = (
            "implementation correlation only — not ABIS Interaction identity"
        )
    if observation_kind:
        result["observation_kind"] = observation_kind
    return result


def merge_connector_provenance(
    base: dict[str, Any] | None,
    connector_metadata: dict[str, Any],
) -> dict[str, Any]:
    """Merge authorized adapter execution metadata into provenance (not Native Result)."""
    merged = dict(base or {})
    for key, value in connector_metadata.items():
        merged[key] = value
    return merged
