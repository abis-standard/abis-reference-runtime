"""Semantic boundary — implementation representations only, not normative ABIS definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class SemanticReference:
    """Opaque upstream semantic object reference — no normative redefinition."""

    object_kind: str
    object_id: str
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InteractionEnvelope:
    """Implementation representation of an upstream ABIS Interaction boundary crossing."""

    interaction_ref: SemanticReference
    capability_ref: SemanticReference | None = None
    decision_ref: SemanticReference | None = None
    constraint_refs: tuple[SemanticReference, ...] = ()


@dataclass(frozen=True)
class SemanticBoundaryInput:
    """Entry point for upstream ABIS semantic objects into Runtime."""

    participant_ref: SemanticReference
    intent_ref: SemanticReference
    interaction: InteractionEnvelope
    metadata: Mapping[str, Any] = field(default_factory=dict)
