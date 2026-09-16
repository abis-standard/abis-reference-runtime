"""Shared profile/descriptor fixtures for reference client tests."""

from __future__ import annotations

from abis_grp_runtime.descriptor.constants import DESCRIPTOR_KIND, DESCRIPTOR_VERSION
from abis_grp_runtime.gateway.reference_profile import PROFILE_KIND


def valid_profile(*, invoke_path: str = "/v1/demo/restaurant/invoke") -> dict:
    return {
        "profile_kind": PROFILE_KIND,
        "profile_version": 2,
        "advertised_interactions": [
            {
                "vertical": "restaurant",
                "operation": "reserve",
                "execution_classes_allowed": ["CONTROLLED_SIMULATOR"],
                "invocation": {"method": "POST", "path": invoke_path},
                "descriptor_path": "/v1/reference-profile/interactions/restaurant/reserve",
            }
        ],
    }


def valid_descriptor(*, invoke_path: str = "/v1/demo/restaurant/invoke") -> dict:
    return {
        "descriptor_kind": DESCRIPTOR_KIND,
        "descriptor_version": DESCRIPTOR_VERSION,
        "structured_input": {
            "required_fields": ["date", "time", "party_size", "seating_type"],
            "optional_fields": ["customer_reference", "idempotency_key", "test_scenario"],
            "field_types": {
                "date": "string",
                "time": "string",
                "party_size": "integer",
                "seating_type": "string",
            },
        },
        "invocation": {"method": "POST", "path": invoke_path},
        "preflight": {"method": "POST", "path": "/v1/demo/restaurant/preflight"},
        "authorization": {"invoke": {"required": True, "scheme": "bearer"}},
    }
