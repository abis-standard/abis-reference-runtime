"""Execution contract — disposition only, not ABIS semantics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExecutionClass(str, Enum):
    """Runtime-owned execution classification."""

    NULL = "NULL"
    FIXTURE = "FIXTURE"
    CONTROLLED_SIMULATOR = "CONTROLLED_SIMULATOR"
    AUTHORIZED_NON_PRODUCTION = "AUTHORIZED_NON_PRODUCTION"
    REAL_EXTERNAL = "REAL_EXTERNAL"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def parse(cls, value: str | ExecutionClass | None) -> ExecutionClass:
        if value is None:
            return cls.UNKNOWN
        if isinstance(value, ExecutionClass):
            return value
        try:
            return cls(value.upper())
        except ValueError:
            return cls.UNKNOWN


class ExecutionPolicy(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


@dataclass(frozen=True)
class ExecutionDisposition:
    """Explicit execution disposition for a request."""

    execution_class: ExecutionClass
    policy: ExecutionPolicy
    reason: str

    @property
    def allowed(self) -> bool:
        return self.policy is ExecutionPolicy.ALLOW


def resolve_execution_disposition(execution_class: ExecutionClass) -> ExecutionDisposition:
    """M-201 baseline: mock-only + authorized non-production egress; REAL_EXTERNAL/UNKNOWN denied."""
    allowed = {
        ExecutionClass.NULL,
        ExecutionClass.FIXTURE,
        ExecutionClass.CONTROLLED_SIMULATOR,
        ExecutionClass.AUTHORIZED_NON_PRODUCTION,
    }
    if execution_class in allowed:
        return ExecutionDisposition(
            execution_class=execution_class,
            policy=ExecutionPolicy.ALLOW,
            reason=f"{execution_class.value} permitted under M-201 mock-only baseline",
        )
    if execution_class is ExecutionClass.REAL_EXTERNAL:
        return ExecutionDisposition(
            execution_class=execution_class,
            policy=ExecutionPolicy.DENY,
            reason="REAL_EXTERNAL denied under M-201 mock-only baseline",
        )
    return ExecutionDisposition(
        execution_class=execution_class,
        policy=ExecutionPolicy.DENY,
        reason="Unknown execution class — fail closed",
    )
