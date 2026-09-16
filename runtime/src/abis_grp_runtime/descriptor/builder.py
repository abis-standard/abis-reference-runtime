"""Build Interaction Descriptor documents from adapter metadata."""

from __future__ import annotations

from typing import Any, Mapping

from abis_grp_runtime.descriptor.constants import (
    DESCRIPTOR_KIND,
    DESCRIPTOR_VERSION,
    STANDARD_DISCLAIMER,
    descriptor_path_for,
)


def build_descriptor(
    *,
    vertical: str,
    operation: str,
    execution_classes_allowed: frozenset[str],
    structured_input: Mapping[str, Any],
    business_system_identifier: str,
    business_system_classification: str = "EXTERNAL_BUSINESS_SYSTEM_TEST_DOUBLE",
) -> dict[str, Any]:
    vertical_norm = vertical.strip().lower()
    operation_norm = operation.strip().lower()
    return {
        "descriptor_kind": DESCRIPTOR_KIND,
        "descriptor_version": DESCRIPTOR_VERSION,
        "authority": {"semantic": "NONE", "normative": "NONE"},
        "vertical": vertical_norm,
        "operation": operation_norm,
        "execution_classes_allowed": sorted(execution_classes_allowed),
        "preflight": {
            "method": "POST",
            "path": f"/v1/demo/{vertical_norm}/preflight",
        },
        "invocation": {
            "method": "POST",
            "path": f"/v1/demo/{vertical_norm}/invoke",
        },
        "authorization": {
            "invoke": {"required": True, "scheme": "bearer"},
        },
        "request_envelope": {
            "required_fields": [
                "agent_id",
                "agent_type",
                "operation",
                "execution_class",
                "correlation_id",
            ],
            "input_field": "input",
            "input_field_alternate": "structured_input",
            "authorization_token": {
                "required": True,
                "transport": "bearer_header_or_body",
            },
        },
        "structured_input": dict(structured_input),
        "native_result": {
            "envelope_fields": [
                "technical_status",
                "external_status",
                "external_identifier",
                "payload",
                "error",
                "timing_ms",
                "source",
            ],
            "payload_opaque": True,
            "outcome_evaluation": "NOT_EVALUATED",
        },
        "business_system": {
            "identifier": business_system_identifier,
            "classification": business_system_classification,
        },
        "disclaimer": dict(STANDARD_DISCLAIMER),
        "descriptor_path": descriptor_path_for(vertical_norm, operation_norm),
    }
