"""Native Result envelope — transport-neutral operational observations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class NativeResultEnvelope:
    """
    Transport-neutral Native Result container.

    Native Result ≠ ABIS Outcome.
    HTTP 200 / CONFIRMED / technical success do NOT automatically imply Outcome SUCCESS.
    """

    technical_status: str
    external_status: str | None = None
    external_identifier: str | None = None
    payload: Mapping[str, Any] = field(default_factory=dict)
    error: Mapping[str, Any] | None = None
    timing_ms: int | None = None
    source: str | None = None

    def implies_outcome_success(self) -> bool:
        """Explicit separation guard — Native Result must not imply Outcome."""
        return False
