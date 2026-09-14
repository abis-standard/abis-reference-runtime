"""Evidence and trace — local/private, not semantic authority."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TraceEvent:
    phase: str
    disposition: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class FoundationTrace:
    """Minimal local trace for M-201 foundation lifecycle."""

    correlation_id: str
    request_id: str
    events: list[TraceEvent] = field(default_factory=list)

    def record(self, phase: str, disposition: str, **detail: Any) -> None:
        self.events.append(TraceEvent(phase=phase, disposition=disposition, detail=dict(detail)))

    def phases(self) -> list[str]:
        return [event.phase for event in self.events]

    def to_dict(self) -> dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "events": [
                {"phase": e.phase, "disposition": e.disposition, "detail": e.detail}
                for e in self.events
            ],
        }
