"""Evidence and trace — local/private, not semantic authority."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

# M-18F: structured resource-observation evidence (optional trace detail).
STRUCTURED_RESOURCE_OBSERVATION_DETAIL_KEY = "structured_resource_observation"
RESOURCE_OBSERVATION_PHASE = "resource_observation"

OBSERVATION_RESULT_OBSERVED = "RESOURCE_OBSERVED"
OBSERVATION_RESULT_NOT_OBSERVED = "RESOURCE_NOT_OBSERVED"
OBSERVATION_RESULT_UNKNOWN = "RESOURCE_OBSERVATION_UNKNOWN"

OBSERVATION_SOURCE_ACTION_RESPONSE = "action_response"
OBSERVATION_SOURCE_LATER_READ = "later_read"
OBSERVATION_SOURCE_NATIVE_OBSERVATION = "native_observation"

OBSERVATION_CAUSE_UNKNOWN = "UNKNOWN"

_PROHIBITED_OBSERVATION_CAUSES = frozenset(
    {
        "DELETED",
        "NEVER_EXISTED",
        "NOT_PERSISTED",
        "PROVIDER_FAILURE",
        "BUSINESS_OUTCOME_FAILURE",
    }
)


@dataclass(frozen=True)
class StructuredResourceObservation:
    """Provider-neutral resource observation evidence (M-18D/M-18F)."""

    subject_ref: str
    observation_source: str
    observation_result: str
    observed_provider_state: str | None = None
    sequence_index: int | None = None
    observation_cause: str | None = None
    local_processing_note: str | None = None
    provider_native_detail: dict[str, Any] | None = None

    def to_detail_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "subject_ref": self.subject_ref,
            "observation_source": self.observation_source,
            "observation_result": self.observation_result,
        }
        if self.observed_provider_state is not None:
            payload["observed_provider_state"] = self.observed_provider_state
        if self.sequence_index is not None:
            payload["sequence_index"] = self.sequence_index
        if self.observation_cause is not None:
            payload["observation_cause"] = self.observation_cause
        if self.local_processing_note is not None:
            payload["local_processing_note"] = self.local_processing_note
        if self.provider_native_detail:
            payload["provider_native_detail"] = dict(self.provider_native_detail)
        return payload


def validate_structured_resource_observation(data: Mapping[str, Any]) -> str | None:
    """Return an error message if invalid; None if acceptable."""
    for key in ("subject_ref", "observation_source", "observation_result"):
        if not str(data.get(key) or "").strip():
            return f"missing required field: {key}"
    result = str(data["observation_result"])
    if result not in (
        OBSERVATION_RESULT_OBSERVED,
        OBSERVATION_RESULT_NOT_OBSERVED,
        OBSERVATION_RESULT_UNKNOWN,
    ):
        return f"invalid observation_result: {result}"
    cause = data.get("observation_cause")
    if cause is not None:
        cause_s = str(cause)
        if cause_s in _PROHIBITED_OBSERVATION_CAUSES:
            return f"prohibited observation_cause: {cause_s}"
    return None


def structured_resource_observation_from_mapping(data: Mapping[str, Any]) -> StructuredResourceObservation | None:
    err = validate_structured_resource_observation(data)
    if err:
        return None
    detail = data.get("provider_native_detail")
    return StructuredResourceObservation(
        subject_ref=str(data["subject_ref"]),
        observation_source=str(data["observation_source"]),
        observation_result=str(data["observation_result"]),
        observed_provider_state=(
            str(data["observed_provider_state"]) if data.get("observed_provider_state") is not None else None
        ),
        sequence_index=int(data["sequence_index"]) if data.get("sequence_index") is not None else None,
        observation_cause=str(data["observation_cause"]) if data.get("observation_cause") is not None else None,
        local_processing_note=(
            str(data["local_processing_note"]) if data.get("local_processing_note") is not None else None
        ),
        provider_native_detail=dict(detail) if isinstance(detail, Mapping) else None,
    )


def _coerce_observation_specs(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if isinstance(raw, Mapping):
        return [dict(raw)]
    if isinstance(raw, list):
        return [dict(item) for item in raw if isinstance(item, Mapping)]
    return []


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

    def record_structured_resource_observation(self, observation: StructuredResourceObservation) -> None:
        """Append one ordered resource-observation evidence event (does not overwrite prior events)."""
        self.events.append(
            TraceEvent(
                phase=RESOURCE_OBSERVATION_PHASE,
                disposition=observation.observation_result,
                detail={STRUCTURED_RESOURCE_OBSERVATION_DETAIL_KEY: observation.to_detail_dict()},
            )
        )

    def structured_resource_observations(self) -> list[StructuredResourceObservation]:
        found: list[StructuredResourceObservation] = []
        for event in self.events:
            if event.phase != RESOURCE_OBSERVATION_PHASE:
                continue
            blob = event.detail.get(STRUCTURED_RESOURCE_OBSERVATION_DETAIL_KEY)
            if not isinstance(blob, Mapping):
                continue
            parsed = structured_resource_observation_from_mapping(blob)
            if parsed is not None:
                found.append(parsed)
        return found

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


def emit_structured_resource_observations_from_native_payload(
    trace: FoundationTrace,
    payload: Mapping[str, Any] | None,
) -> None:
    """Emit optional observation events when native payload carries structured evidence."""
    if not payload:
        return
    for spec in _coerce_observation_specs(payload.get(STRUCTURED_RESOURCE_OBSERVATION_DETAIL_KEY)):
        observation = structured_resource_observation_from_mapping(spec)
        if observation is not None:
            trace.record_structured_resource_observation(observation)
