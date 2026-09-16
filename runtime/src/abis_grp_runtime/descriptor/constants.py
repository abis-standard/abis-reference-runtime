"""Interaction Descriptor constants."""

from __future__ import annotations

from typing import Any

DESCRIPTOR_KIND = "abis-reference-runtime-interaction-descriptor"
DESCRIPTOR_VERSION = 1

STANDARD_DISCLAIMER: dict[str, bool] = {
    "implementation_metadata_only": True,
    "not_abis_capability": True,
    "not_abis_intent": True,
    "not_abis_interaction_definition": True,
    "not_conformance": True,
    "not_outcome_prediction": True,
    "native_result_not_outcome": True,
}


def descriptor_path_for(vertical: str, operation: str) -> str:
    return f"/v1/reference-profile/interactions/{vertical.strip().lower()}/{operation.strip().lower()}"
