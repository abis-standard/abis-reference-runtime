"""External demo gateway errors — transport boundary only."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class GatewayErrorCode(str, Enum):
    AUTHENTICATION_DENIED = "AUTHENTICATION_DENIED"
    REQUEST_INVALID = "REQUEST_INVALID"
    OPERATION_DENIED = "OPERATION_DENIED"
    EXECUTION_CLASS_DENIED = "EXECUTION_CLASS_DENIED"
    VERTICAL_DENIED = "VERTICAL_DENIED"
    CONTROL_PLANE_DENIED = "CONTROL_PLANE_DENIED"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"


@dataclass(frozen=True)
class GatewayError:
    code: GatewayErrorCode
    message: str
    http_status: int
    detail: dict[str, Any] | None = None

    def to_response(self, *, correlation_id: str | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {
            "transport_status": "REJECTED",
            "error": {"code": self.code.value, "message": self.message},
        }
        if correlation_id:
            body["correlation_id"] = correlation_id
        if self.detail:
            body["error"]["detail"] = self.detail
        return body
