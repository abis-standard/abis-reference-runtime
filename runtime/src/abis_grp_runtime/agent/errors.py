"""Agent contract errors — implementation-level, not ABIS semantics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AgentContractErrorCode(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    EXECUTION_CLASS_DENIED = "EXECUTION_CLASS_DENIED"
    RUNTIME_ERROR = "RUNTIME_ERROR"


@dataclass(frozen=True)
class AgentErrorEnvelope:
    code: AgentContractErrorCode
    message: str
    detail: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"code": self.code.value, "message": self.message}
        if self.detail:
            payload["detail"] = self.detail
        return payload
