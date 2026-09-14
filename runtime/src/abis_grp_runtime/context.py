"""Runtime request context — operational metadata only."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from abis_grp_runtime.execution import ExecutionClass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class RuntimeRequestContext:
    """Implementation-owned request context. Does not redefine ABIS Participant or Intent."""

    correlation_id: str
    request_id: str
    agent_id: str
    execution_class: ExecutionClass
    timestamp: datetime
    trace_context: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        agent_id: str,
        execution_class: ExecutionClass | str,
        correlation_id: str | None = None,
        request_id: str | None = None,
        trace_context: dict[str, Any] | None = None,
    ) -> RuntimeRequestContext:
        parsed = (
            execution_class
            if isinstance(execution_class, ExecutionClass)
            else ExecutionClass.parse(execution_class)
        )
        return cls(
            correlation_id=correlation_id or str(uuid4()),
            request_id=request_id or str(uuid4()),
            agent_id=agent_id,
            execution_class=parsed,
            timestamp=_utc_now(),
            trace_context=dict(trace_context or {}),
        )
