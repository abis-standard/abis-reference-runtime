"""Outcome interpreter boundary — interface only at M-201."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping

from abis_grp_runtime.native_result import NativeResultEnvelope
from abis_grp_runtime.semantic import SemanticBoundaryInput


@dataclass(frozen=True)
class OutcomeInterpretationDisposition:
    """Implementation disposition — not normative ABIS Outcome definition."""

    disposition: str
    reason: str
    outcome_ref: Mapping[str, Any] | None = None


class OutcomeInterpreterPort(ABC):
    """Boundary for future outcome determination — not implemented in Reference Runtime v0.1."""

    @abstractmethod
    def interpret(
        self,
        semantic_input: SemanticBoundaryInput,
        native_result: NativeResultEnvelope | None,
    ) -> OutcomeInterpretationDisposition:
        ...


class NullOutcomeInterpreter(OutcomeInterpreterPort):
    """M-201 stub — records boundary crossing without reverse mapping HOW."""

    def interpret(
        self,
        semantic_input: SemanticBoundaryInput,
        native_result: NativeResultEnvelope | None,
    ) -> OutcomeInterpretationDisposition:
        return OutcomeInterpretationDisposition(
            disposition="NOT_EVALUATED",
            reason="M-201 stub — outcome determination deferred",
            outcome_ref={
                "interaction_id": semantic_input.interaction.interaction_ref.object_id,
                "native_result_observed": native_result is not None,
            },
        )
