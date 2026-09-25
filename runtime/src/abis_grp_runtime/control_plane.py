"""Minimal control plane — policy enforcement, not ABIS semantics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from abis_grp_runtime.execution import ExecutionClass, ExecutionPolicy


class ControlDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


@dataclass(frozen=True)
class ControlPlaneVerdict:
    decision: ControlDecision
    control: str
    reason: str


_M201_FIREWALL: dict[str, ControlDecision] = {
    "REAL_EXECUTION": ControlDecision.DENY,
    "REAL_BOOKING": ControlDecision.DENY,
    "REAL_PAYMENT": ControlDecision.DENY,
    "REAL_BUSINESS_API_MUTATION": ControlDecision.DENY,
    "UNAPPROVED_EXTERNAL_EGRESS": ControlDecision.DENY,
    "CONTROLLED_SIMULATOR": ControlDecision.ALLOW,
    "AUTHORIZED_NON_PRODUCTION_EGRESS": ControlDecision.ALLOW,
    "NULL_EXECUTOR": ControlDecision.ALLOW,
    "FIXTURE_EXECUTION": ControlDecision.ALLOW,
    "UNKNOWN_EXECUTION_CLASS": ControlDecision.DENY,
}


_EXECUTION_CLASS_CONTROLS: dict[ExecutionClass, tuple[str, ...]] = {
    ExecutionClass.NULL: ("NULL_EXECUTOR",),
    ExecutionClass.FIXTURE: ("FIXTURE_EXECUTION",),
    ExecutionClass.CONTROLLED_SIMULATOR: ("CONTROLLED_SIMULATOR",),
    ExecutionClass.AUTHORIZED_NON_PRODUCTION: ("AUTHORIZED_NON_PRODUCTION_EGRESS",),
    ExecutionClass.REAL_EXTERNAL: ("REAL_EXECUTION", "REAL_BUSINESS_API_MUTATION", "UNAPPROVED_EXTERNAL_EGRESS"),
    ExecutionClass.UNKNOWN: ("UNKNOWN_EXECUTION_CLASS",),
}


def evaluate_control_plane(execution_class: ExecutionClass) -> list[ControlPlaneVerdict]:
    """Evaluate all relevant firewall controls for an execution class."""
    verdicts: list[ControlPlaneVerdict] = []
    controls = _EXECUTION_CLASS_CONTROLS.get(execution_class, ("UNKNOWN_EXECUTION_CLASS",))
    for control in controls:
        decision = _M201_FIREWALL.get(control, ControlDecision.DENY)
        verdicts.append(
            ControlPlaneVerdict(
                decision=decision,
                control=control,
                reason=f"{control} -> {decision.value}",
            )
        )
    if execution_class is ExecutionClass.REAL_EXTERNAL:
        for extra in ("REAL_BOOKING", "REAL_PAYMENT"):
            verdicts.append(
                ControlPlaneVerdict(
                    decision=_M201_FIREWALL[extra],
                    control=extra,
                    reason=f"{extra} -> DENY",
                )
            )
    return verdicts


def control_plane_allows(execution_class: ExecutionClass) -> tuple[bool, str]:
    """Return whether control plane permits the execution class (fail closed)."""
    if execution_class is ExecutionClass.UNKNOWN:
        return False, "UNKNOWN_EXECUTION_CLASS fail closed"
    verdicts = evaluate_control_plane(execution_class)
    for verdict in verdicts:
        if verdict.decision is ControlDecision.DENY:
            return False, verdict.reason
    return True, "mock-only firewall pass"
