"""Expected and observed state models — implementation representations only."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExpectedState:
    """Implementation-owned expected business state — not normative ABIS semantics."""

    date: str | None = None
    time: str | None = None
    party_size: int | None = None
    seating_type: str | None = None
    status: str | None = None

    def comparable_fields(self) -> tuple[str, ...]:
        fields: list[str] = []
        if self.date is not None:
            fields.append("date")
        if self.time is not None:
            fields.append("time")
        if self.party_size is not None:
            fields.append("party_size")
        if self.seating_type is not None:
            fields.append("seating_type")
        if self.status is not None:
            fields.append("status")
        return tuple(fields)

    def value(self, field_name: str) -> Any:
        return getattr(self, field_name)


@dataclass(frozen=True)
class ObservedState:
    """Observed business state extracted from Native Result content only."""

    date: str | None = None
    time: str | None = None
    party_size: int | None = None
    seating_type: str | None = None
    status: str | None = None
    reservation_id: str | None = None
    partial: bool = False

    def value(self, field_name: str) -> Any:
        return getattr(self, field_name)


@dataclass(frozen=True)
class ComparisonResult:
    """Derived testbed outcome evaluation — not an ABIS Outcome verdict."""

    evaluation: str
    pattern: str
    matched_fields: tuple[str, ...]
    mismatched_fields: tuple[str, ...]
    expected_values: dict[str, Any]
    observed_values: dict[str, Any]
    technical_disposition: str
    native_status: str | None
    correlation_id: str
    semantic_authority: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluation": self.evaluation,
            "pattern": self.pattern,
            "matched_fields": list(self.matched_fields),
            "mismatched_fields": list(self.mismatched_fields),
            "expected_values": dict(self.expected_values),
            "observed_values": dict(self.observed_values),
            "technical_disposition": self.technical_disposition,
            "native_status": self.native_status,
            "correlation_id": self.correlation_id,
            "semantic_authority": self.semantic_authority,
        }


@dataclass
class EvaluationTrace:
    """Private testbed evaluation trace — not Conformance evidence."""

    correlation_id: str
    expected_state: ExpectedState
    native_result_reference: dict[str, Any]
    compared_fields: tuple[str, ...] = ()
    matched_fields: tuple[str, ...] = ()
    mismatched_fields: tuple[str, ...] = ()
    evaluation_disposition: str = ""
    pattern: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "expected_state": {
                "date": self.expected_state.date,
                "time": self.expected_state.time,
                "party_size": self.expected_state.party_size,
                "seating_type": self.expected_state.seating_type,
                "status": self.expected_state.status,
            },
            "native_result_reference": {
                "transport_ok": self.native_result_reference.get("transport_ok"),
                "status": self.native_result_reference.get("status"),
                "reservation_id": self.native_result_reference.get("reservation_id"),
            },
            "compared_fields": list(self.compared_fields),
            "matched_fields": list(self.matched_fields),
            "mismatched_fields": list(self.mismatched_fields),
            "evaluation_disposition": self.evaluation_disposition,
            "pattern": self.pattern,
            "semantic_authority": "NONE",
        }
