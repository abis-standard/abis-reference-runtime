"""Domain models and Native Result envelope helpers.

semantic_authority = NONE. Never include ABIS outcome/verdict fields.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

BUSINESS_SYSTEM_ID = "abis-demo-restaurant-simulator"
RESTAURANT_NAME = "ABIS Demo Restaurant"
CLASSIFICATION = "EXTERNAL_BUSINESS_SYSTEM_TEST_DOUBLE"
SEMANTIC_AUTHORITY = "NONE"

SEATING_TABLE = "TABLE"
SEATING_PRIVATE_ROOM = "PRIVATE_ROOM"
SEATING_TYPES = (SEATING_TABLE, SEATING_PRIVATE_ROOM)

STATUS_CONFIRMED = "CONFIRMED"
STATUS_PENDING = "PENDING"
STATUS_CANCELLED = "CANCELLED"
STATUS_REJECTED = "REJECTED"
NATIVE_STATUSES = (
    STATUS_CONFIRMED,
    STATUS_PENDING,
    STATUS_CANCELLED,
    STATUS_REJECTED,
)

# Forbidden ABIS-outcome keys — must never appear in Native Result JSON.
FORBIDDEN_ABIS_KEYS = frozenset(
    {
        "abis_outcome",
        "abis_verdict",
        "abis_mismatch",
        "outcome_verification",
        "ABIS_SUCCESS",
        "ABIS_FAILURE",
        "ABIS_MISMATCH",
    }
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_reservation_id() -> str:
    return f"TEST-RSV-{uuid4().hex[:12].upper()}"


def new_customer_ref(prefix: str = "TEST-CUST") -> str:
    return f"{prefix}-{uuid4().hex[:8].upper()}"


def native_result(
    *,
    operation: str,
    status: Optional[str],
    transport_ok: bool,
    requested: Optional[Dict[str, Any]] = None,
    actual: Optional[Dict[str, Any]] = None,
    reservation_id: Optional[str] = None,
    error: Optional[str] = None,
    reason: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    idempotent_replay: Optional[bool] = None,
    test_scenario: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a Business System Native Result envelope (not an ABIS Outcome)."""
    body: Dict[str, Any] = {
        "business_system": BUSINESS_SYSTEM_ID,
        "restaurant": RESTAURANT_NAME,
        "operation": operation,
        "status": status,
        "transport_ok": bool(transport_ok),
        "reservation_id": reservation_id,
        "requested": deepcopy(requested) if requested is not None else None,
        "actual": deepcopy(actual) if actual is not None else None,
        "error": error,
        "reason": reason,
        "timestamp": utc_now_iso(),
        "classification": CLASSIFICATION,
        "semantic_authority": SEMANTIC_AUTHORITY,
    }
    if idempotency_key is not None:
        body["idempotency_key"] = idempotency_key
    if idempotent_replay is not None:
        body["idempotent_replay"] = idempotent_replay
    if test_scenario is not None:
        body["test_scenario"] = test_scenario
    if extra:
        for k, v in extra.items():
            if k in FORBIDDEN_ABIS_KEYS:
                continue
            body[k] = v
    # Hard strip any accidental ABIS keys
    for bad in FORBIDDEN_ABIS_KEYS:
        body.pop(bad, None)
    return body


def reservation_to_actual(rec: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "reservation_id": rec.get("reservation_id"),
        "date": rec.get("date"),
        "time": rec.get("time"),
        "party_size": rec.get("party_size"),
        "seating_type": rec.get("seating_type"),
        "customer_reference": rec.get("customer_reference"),
        "status": rec.get("status"),
    }


def assert_no_abis_keys(obj: Any, path: str = "$") -> List[str]:
    """Return list of paths where forbidden ABIS keys appear."""
    found: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in FORBIDDEN_ABIS_KEYS or str(k).upper() in {
                "ABIS_SUCCESS",
                "ABIS_FAILURE",
                "ABIS_MISMATCH",
            }:
                found.append(f"{path}.{k}")
            found.extend(assert_no_abis_keys(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(assert_no_abis_keys(v, f"{path}[{i}]"))
    return found
