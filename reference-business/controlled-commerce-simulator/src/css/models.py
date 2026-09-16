"""CSS domain helpers — semantic_authority = NONE."""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import uuid4

BUSINESS_SYSTEM_ID = "abis-demo-commerce-simulator"
CLASSIFICATION = "EXTERNAL_BUSINESS_SYSTEM_TEST_DOUBLE"
SEMANTIC_AUTHORITY = "NONE"

STATUS_ORDER_SUBMITTED = "ORDER_SUBMITTED"

SYNTHETIC_SKUS = {
    "SKU-DEMO-001": {"name": "Demo Widget", "available": True},
    "SKU-DEMO-002": {"name": "Demo Gadget", "available": True},
    "SKU-DEMO-UNAVAILABLE": {"name": "Unavailable Demo Item", "available": False},
}


def new_order_id() -> str:
    return f"ORD-DEMO-{uuid4().hex[:8].upper()}"


def native_result(
    *,
    operation: str,
    status: Optional[str],
    transport_ok: bool,
    requested: Dict[str, Any],
    order_id: Optional[str] = None,
    error: Optional[str] = None,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "operation": operation,
        "status": status,
        "transport_ok": transport_ok,
        "requested": requested,
        "business_system": BUSINESS_SYSTEM_ID,
        "classification": CLASSIFICATION,
        "semantic_authority": SEMANTIC_AUTHORITY,
    }
    if order_id:
        payload["order_id"] = order_id
    if error:
        payload["error"] = error
    if reason:
        payload["reason"] = reason
    return payload
