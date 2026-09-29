"""Sanitized HBX external execution observability — no raw provider content."""

from __future__ import annotations

from typing import Any

ERROR_CATEGORY_AUTH_REJECTION = "AUTH_REJECTION"
ERROR_CATEGORY_PROVIDER_HTTP_REJECTION = "PROVIDER_HTTP_REJECTION"
ERROR_CATEGORY_PROVIDER_SERVER_ERROR = "PROVIDER_SERVER_ERROR"
ERROR_CATEGORY_CONTENT_TYPE_REJECTION = "CONTENT_TYPE_REJECTION"
ERROR_CATEGORY_MALFORMED_EXTERNAL_RESPONSE = "MALFORMED_EXTERNAL_RESPONSE"
ERROR_CATEGORY_RESPONSE_MAPPING_FAILURE = "RESPONSE_MAPPING_FAILURE"
ERROR_CATEGORY_TRANSPORT_FAILURE = "TRANSPORT_FAILURE"


def http_status_class(http_status: int | None) -> str | None:
    if http_status is None:
        return None
    if 200 <= http_status < 300:
        return "2XX"
    if 400 <= http_status < 500:
        return "4XX"
    if 500 <= http_status < 600:
        return "5XX"
    return None


def error_category_for_code(error_code: str) -> str:
    code = error_code.strip().upper()
    if code == "AUTH_REJECTED":
        return ERROR_CATEGORY_AUTH_REJECTION
    if code == "HTTP_4XX":
        return ERROR_CATEGORY_PROVIDER_HTTP_REJECTION
    if code == "HTTP_5XX":
        return ERROR_CATEGORY_PROVIDER_SERVER_ERROR
    if code == "UNEXPECTED_CONTENT_TYPE":
        return ERROR_CATEGORY_CONTENT_TYPE_REJECTION
    if code == "MALFORMED_EXTERNAL_RESPONSE":
        return ERROR_CATEGORY_MALFORMED_EXTERNAL_RESPONSE
    if code == "RESPONSE_MAPPING_FAILED":
        return ERROR_CATEGORY_RESPONSE_MAPPING_FAILURE
    return ERROR_CATEGORY_TRANSPORT_FAILURE


def build_external_execution_observability(
    *,
    http_status: int | None = None,
    error_code: str | None = None,
    response_json_parse_succeeded: bool | None = None,
    response_mapping_succeeded: bool | None = None,
    provider_native_status_present: bool | None = None,
    external_identifier_present: bool | None = None,
) -> dict[str, Any]:
    """Build a fixed-shape observability block safe for provenance and gateway evidence."""
    block: dict[str, Any] = {}
    if http_status is not None:
        block["http_status"] = int(http_status)
        status_class = http_status_class(http_status)
        if status_class is not None:
            block["http_status_class"] = status_class
    if error_code:
        block["error_code"] = error_code
        block["error_category"] = error_category_for_code(error_code)
    if response_json_parse_succeeded is not None:
        block["response_json_parse_succeeded"] = bool(response_json_parse_succeeded)
    if response_mapping_succeeded is not None:
        block["response_mapping_succeeded"] = bool(response_mapping_succeeded)
    if provider_native_status_present is not None:
        block["provider_native_status_present"] = bool(provider_native_status_present)
    if external_identifier_present is not None:
        block["external_identifier_present"] = bool(external_identifier_present)
    return block
