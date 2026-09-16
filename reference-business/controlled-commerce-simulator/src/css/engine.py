"""In-process commerce engine — synthetic order intake only."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional

from css.models import (
    STATUS_ORDER_SUBMITTED,
    SYNTHETIC_SKUS,
    native_result,
    new_order_id,
)

SCENARIO_NORMAL_SUCCESS = "NORMAL_SUCCESS"
SCENARIO_UNKNOWN_SKU = "UNKNOWN_SKU"
SCENARIO_UNAVAILABLE = "UNAVAILABLE"
SCENARIO_INVALID_QUANTITY = "INVALID_QUANTITY"


class CommerceEngine:
    """Controlled Commerce Simulator engine."""

    def __init__(self) -> None:
        self._orders: Dict[str, Dict[str, Any]] = {}

    def submit_order(
        self,
        sku_id: str,
        quantity: int,
        *,
        idempotency_key: Optional[str] = None,
        test_scenario: Optional[str] = None,
    ) -> Dict[str, Any]:
        requested = {"sku_id": sku_id, "quantity": quantity, "idempotency_key": idempotency_key}
        scenario = (test_scenario or SCENARIO_NORMAL_SUCCESS).strip().upper()

        if scenario == SCENARIO_INVALID_QUANTITY or quantity <= 0:
            return native_result(
                operation="submit_order",
                status=None,
                transport_ok=False,
                requested=requested,
                error="INVALID_QUANTITY",
                reason="quantity must be positive",
            )

        if scenario == SCENARIO_UNKNOWN_SKU or sku_id not in SYNTHETIC_SKUS:
            return native_result(
                operation="submit_order",
                status=None,
                transport_ok=False,
                requested=requested,
                error="UNKNOWN_SKU",
                reason=f"Unknown sku_id: {sku_id}",
            )

        catalog = SYNTHETIC_SKUS[sku_id]
        if scenario == SCENARIO_UNAVAILABLE or not catalog.get("available"):
            return native_result(
                operation="submit_order",
                status=None,
                transport_ok=False,
                requested=requested,
                error="SKU_UNAVAILABLE",
                reason="Synthetic SKU not available",
            )

        if idempotency_key and idempotency_key in self._orders:
            existing = self._orders[idempotency_key]
            return native_result(
                operation="submit_order",
                status=STATUS_ORDER_SUBMITTED,
                transport_ok=True,
                requested=requested,
                order_id=existing["order_id"],
            )

        order_id = new_order_id()
        record = {
            "order_id": order_id,
            "sku_id": sku_id,
            "quantity": quantity,
            "status": STATUS_ORDER_SUBMITTED,
        }
        key = idempotency_key or _fingerprint(requested)
        self._orders[key] = record

        return native_result(
            operation="submit_order",
            status=STATUS_ORDER_SUBMITTED,
            transport_ok=True,
            requested=requested,
            order_id=order_id,
        )


def _fingerprint(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
