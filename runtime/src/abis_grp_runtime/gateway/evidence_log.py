"""Safe gateway evidence logging — no secrets, no PII."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_LOCK = threading.Lock()


def _safe_record(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "correlation_id": record.get("correlation_id"),
        "agent_type": record.get("agent_type"),
        "vertical": record.get("vertical"),
        "operation": record.get("operation"),
        "authorization_disposition": record.get("authorization_disposition"),
        "execution_disposition": record.get("execution_disposition"),
        "native_status": record.get("native_status"),
        "outcome_evaluation": record.get("outcome_evaluation"),
        "mismatched_fields": record.get("mismatched_fields"),
        "http_status": record.get("http_status"),
        "transport_status": record.get("transport_status"),
        "gateway_error_code": record.get("gateway_error_code"),
    }


def append_evidence(path: str | None, record: Mapping[str, Any]) -> None:
    if not path:
        return
    line = json.dumps(_safe_record(record), sort_keys=True)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with target.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
