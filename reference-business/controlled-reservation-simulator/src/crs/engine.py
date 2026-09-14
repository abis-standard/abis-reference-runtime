"""In-process reservation engine (callable without HTTP server).

Reports Business System Native Result only. semantic_authority = NONE.
Never emits ABIS Outcome verdicts.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

from crs import inventory
from crs.models import (
    SEATING_PRIVATE_ROOM,
    SEATING_TABLE,
    STATUS_CANCELLED,
    STATUS_CONFIRMED,
    STATUS_PENDING,
    STATUS_REJECTED,
    native_result,
    new_reservation_id,
    reservation_to_actual,
)
from crs.scenarios import (
    ALL_SCENARIOS,
    SCENARIO_BUSINESS_REJECTED,
    SCENARIO_CONSTRAINT_MISMATCH,
    SCENARIO_DUPLICATE_IDEMPOTENT,
    SCENARIO_NO_AVAILABILITY,
    SCENARIO_NORMAL_SUCCESS,
    SCENARIO_PARTIAL_RESULT,
    SCENARIO_PENDING,
    SCENARIO_TECHNICAL_ERROR,
    SCENARIO_TECHNICAL_SUCCESS_BUSINESS_MISMATCH,
    SCENARIO_TECHNICAL_SUCCESS_SEATING_MISMATCH,
    SCENARIO_TECHNICAL_SUCCESS_TIME_MISMATCH,
    SCENARIO_TIMEOUT,
    normalize_scenario,
)
from crs.store import JsonFileStore


def _fingerprint(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ReservationEngine:
    """Controlled Reservation Simulator engine."""

    def __init__(self, data_dir: str | Path = "./data") -> None:
        self.store = JsonFileStore(data_dir)

    # --- availability -------------------------------------------------
    def availability(
        self,
        date: str,
        party_size: int,
        preferred_time: Optional[str] = None,
        seating_type: Optional[str] = None,
        test_scenario: Optional[str] = None,
    ) -> Dict[str, Any]:
        scenario = normalize_scenario(test_scenario)
        requested = {
            "date": date,
            "party_size": party_size,
            "preferred_time": preferred_time,
            "seating_type": seating_type,
        }
        if scenario and scenario not in ALL_SCENARIOS:
            return native_result(
                operation="availability",
                status=None,
                transport_ok=False,
                requested=requested,
                error="UNKNOWN_TEST_SCENARIO",
                reason=f"Unknown test_scenario: {scenario}",
                test_scenario=scenario,
            )
        if scenario == SCENARIO_TECHNICAL_ERROR:
            return native_result(
                operation="availability",
                status=None,
                transport_ok=False,
                requested=requested,
                error="TECHNICAL_ERROR",
                reason="Simulated technical error",
                test_scenario=scenario,
            )
        if scenario == SCENARIO_TIMEOUT:
            return native_result(
                operation="availability",
                status=None,
                transport_ok=False,
                requested=requested,
                error="TIMEOUT",
                reason="Simulated timeout (immediate Native Result; no sleep)",
                test_scenario=scenario,
            )
        if scenario == SCENARIO_NO_AVAILABILITY:
            return native_result(
                operation="availability",
                status=None,
                transport_ok=True,
                requested=requested,
                actual={"slots": []},
                reason="NO_AVAILABILITY",
                test_scenario=scenario,
                extra={"slots": []},
            )

        slots = inventory.query_availability(date, party_size, preferred_time, seating_type)
        return native_result(
            operation="availability",
            status=None,
            transport_ok=True,
            requested=requested,
            actual={"slots": slots},
            test_scenario=scenario,
            extra={"slots": slots},
        )

    # --- reserve ------------------------------------------------------
    def reserve(
        self,
        date: str,
        time: str,
        party_size: int,
        seating_type: str,
        customer_reference: str,
        idempotency_key: str,
        test_scenario: Optional[str] = None,
    ) -> Dict[str, Any]:
        scenario = normalize_scenario(test_scenario)
        requested = {
            "date": date,
            "time": time,
            "party_size": party_size,
            "seating_type": seating_type,
            "customer_reference": customer_reference,
        }
        fp_payload = {
            "date": date,
            "time": time,
            "party_size": party_size,
            "seating_type": seating_type,
            "customer_reference": customer_reference,
        }
        fp = _fingerprint(fp_payload)

        if scenario and scenario not in ALL_SCENARIOS:
            return native_result(
                operation="reserve",
                status=STATUS_REJECTED,
                transport_ok=False,
                requested=requested,
                error="UNKNOWN_TEST_SCENARIO",
                reason=f"Unknown test_scenario: {scenario}",
                idempotency_key=idempotency_key,
                test_scenario=scenario,
            )

        # Idempotency check (also used by DUPLICATE_IDEMPOTENT scenario)
        existing = self.store.get_idempotency(idempotency_key)
        if existing is not None:
            if existing["request_fingerprint"] == fp or scenario == SCENARIO_DUPLICATE_IDEMPOTENT:
                replay = deepcopy(existing["result"])
                replay["idempotent_replay"] = True
                replay["idempotency_key"] = idempotency_key
                if scenario:
                    replay["test_scenario"] = scenario
                replay["timestamp"] = native_result(
                    operation="reserve", status=None, transport_ok=True
                )["timestamp"]
                return replay
            return native_result(
                operation="reserve",
                status=STATUS_REJECTED,
                transport_ok=True,
                requested=requested,
                error="IDEMPOTENCY_CONFLICT",
                reason="Same idempotency_key with conflicting request",
                idempotency_key=idempotency_key,
                idempotent_replay=False,
                test_scenario=scenario,
            )

        if scenario == SCENARIO_TECHNICAL_ERROR:
            return native_result(
                operation="reserve",
                status=None,
                transport_ok=False,
                requested=requested,
                error="TECHNICAL_ERROR",
                reason="Simulated technical error",
                idempotency_key=idempotency_key,
                test_scenario=scenario,
            )
        if scenario == SCENARIO_TIMEOUT:
            # Simulated timeout — return immediately (do NOT sleep).
            return native_result(
                operation="reserve",
                status=None,
                transport_ok=False,
                requested=requested,
                error="TIMEOUT",
                reason="Simulated timeout (immediate Native Result; no sleep)",
                idempotency_key=idempotency_key,
                test_scenario=scenario,
            )
        if scenario == SCENARIO_NO_AVAILABILITY:
            return native_result(
                operation="reserve",
                status=STATUS_REJECTED,
                transport_ok=True,
                requested=requested,
                error="NO_AVAILABILITY",
                reason="No availability for requested slot",
                idempotency_key=idempotency_key,
                test_scenario=scenario,
            )
        if scenario == SCENARIO_CONSTRAINT_MISMATCH:
            return native_result(
                operation="reserve",
                status=STATUS_REJECTED,
                transport_ok=True,
                requested=requested,
                error="CONSTRAINT_MISMATCH",
                reason="Party size or seating constraint not satisfiable",
                idempotency_key=idempotency_key,
                test_scenario=scenario,
            )
        if scenario == SCENARIO_BUSINESS_REJECTED:
            return native_result(
                operation="reserve",
                status=STATUS_REJECTED,
                transport_ok=True,
                requested=requested,
                error="BUSINESS_REJECTED",
                reason="Business policy rejected the reservation",
                idempotency_key=idempotency_key,
                test_scenario=scenario,
            )
        if scenario == SCENARIO_PARTIAL_RESULT:
            rid = new_reservation_id()
            # Partial: confirmed time but seating omitted / capacity note only
            actual = {
                "reservation_id": rid,
                "date": date,
                "time": time,
                "party_size": party_size,
                "seating_type": None,
                "status": STATUS_CONFIRMED,
                "partial": True,
            }
            rec = {
                "reservation_id": rid,
                "date": date,
                "time": time,
                "party_size": party_size,
                "seating_type": seating_type,
                "customer_reference": customer_reference,
                "status": STATUS_CONFIRMED,
                "partial": True,
            }
            self.store.put_reservation(rid, rec)
            result = native_result(
                operation="reserve",
                status=STATUS_CONFIRMED,
                transport_ok=True,
                requested=requested,
                actual=actual,
                reservation_id=rid,
                reason="PARTIAL_RESULT",
                idempotency_key=idempotency_key,
                idempotent_replay=False,
                test_scenario=scenario,
            )
            self.store.put_idempotency(idempotency_key, fp, rid, result)
            return result
        if scenario == SCENARIO_PENDING:
            rid = new_reservation_id()
            rec = {
                "reservation_id": rid,
                "date": date,
                "time": time,
                "party_size": party_size,
                "seating_type": seating_type,
                "customer_reference": customer_reference,
                "status": STATUS_PENDING,
            }
            self.store.put_reservation(rid, rec)
            result = native_result(
                operation="reserve",
                status=STATUS_PENDING,
                transport_ok=True,
                requested=requested,
                actual=reservation_to_actual(rec),
                reservation_id=rid,
                reason="PENDING",
                idempotency_key=idempotency_key,
                idempotent_replay=False,
                test_scenario=scenario,
            )
            self.store.put_idempotency(idempotency_key, fp, rid, result)
            return result
        if scenario == SCENARIO_TECHNICAL_SUCCESS_TIME_MISMATCH:
            rid = new_reservation_id()
            actual_time = "19:30"
            rec = {
                "reservation_id": rid,
                "date": date,
                "time": actual_time,
                "party_size": party_size,
                "seating_type": seating_type,
                "customer_reference": customer_reference,
                "status": STATUS_CONFIRMED,
            }
            self.store.put_reservation(rid, rec)
            result = native_result(
                operation="reserve",
                status=STATUS_CONFIRMED,
                transport_ok=True,
                requested=requested,
                actual=reservation_to_actual(rec),
                reservation_id=rid,
                reason="TECHNICAL_SUCCESS_TIME_MISMATCH",
                idempotency_key=idempotency_key,
                idempotent_replay=False,
                test_scenario=scenario,
            )
            self.store.put_idempotency(idempotency_key, fp, rid, result)
            return result
        if scenario == SCENARIO_TECHNICAL_SUCCESS_SEATING_MISMATCH:
            rid = new_reservation_id()
            actual_seating = SEATING_TABLE
            rec = {
                "reservation_id": rid,
                "date": date,
                "time": time,
                "party_size": party_size,
                "seating_type": actual_seating,
                "customer_reference": customer_reference,
                "status": STATUS_CONFIRMED,
            }
            self.store.put_reservation(rid, rec)
            result = native_result(
                operation="reserve",
                status=STATUS_CONFIRMED,
                transport_ok=True,
                requested=requested,
                actual=reservation_to_actual(rec),
                reservation_id=rid,
                reason="TECHNICAL_SUCCESS_SEATING_MISMATCH",
                idempotency_key=idempotency_key,
                idempotent_replay=False,
                test_scenario=scenario,
            )
            self.store.put_idempotency(idempotency_key, fp, rid, result)
            return result
        if scenario == SCENARIO_TECHNICAL_SUCCESS_BUSINESS_MISMATCH:
            # Golden: request 19:00 / 4 / PRIVATE_ROOM → actual 19:30 / 4 / TABLE
            # transport_ok true, status CONFIRMED. MUST NOT label ABIS MISMATCH.
            rid = new_reservation_id()
            actual_time = "19:30"
            actual_seating = SEATING_TABLE
            rec = {
                "reservation_id": rid,
                "date": date,
                "time": actual_time,
                "party_size": party_size,
                "seating_type": actual_seating,
                "customer_reference": customer_reference,
                "status": STATUS_CONFIRMED,
            }
            self.store.put_reservation(rid, rec)
            result = native_result(
                operation="reserve",
                status=STATUS_CONFIRMED,
                transport_ok=True,
                requested=requested,
                actual=reservation_to_actual(rec),
                reservation_id=rid,
                reason="TECHNICAL_SUCCESS_BUSINESS_MISMATCH",
                idempotency_key=idempotency_key,
                idempotent_replay=False,
                test_scenario=scenario,
            )
            self.store.put_idempotency(idempotency_key, fp, rid, result)
            return result

        # NORMAL_SUCCESS or no scenario — inventory-gated
        if scenario in (None, SCENARIO_NORMAL_SUCCESS, SCENARIO_DUPLICATE_IDEMPOTENT):
            slot = inventory.find_slot(date, time, seating_type)
            if not inventory.is_slot_available(slot, party_size):
                return native_result(
                    operation="reserve",
                    status=STATUS_REJECTED,
                    transport_ok=True,
                    requested=requested,
                    error="NO_AVAILABILITY",
                    reason="Requested slot unavailable or insufficient capacity",
                    idempotency_key=idempotency_key,
                    test_scenario=scenario,
                )
            rid = new_reservation_id()
            rec = {
                "reservation_id": rid,
                "date": date,
                "time": time,
                "party_size": party_size,
                "seating_type": seating_type,
                "customer_reference": customer_reference,
                "status": STATUS_CONFIRMED,
            }
            self.store.put_reservation(rid, rec)
            result = native_result(
                operation="reserve",
                status=STATUS_CONFIRMED,
                transport_ok=True,
                requested=requested,
                actual=reservation_to_actual(rec),
                reservation_id=rid,
                idempotency_key=idempotency_key,
                idempotent_replay=False,
                test_scenario=scenario,
            )
            self.store.put_idempotency(idempotency_key, fp, rid, result)
            return result

        return native_result(
            operation="reserve",
            status=STATUS_REJECTED,
            transport_ok=True,
            requested=requested,
            error="UNHANDLED_SCENARIO",
            reason=f"Unhandled scenario: {scenario}",
            idempotency_key=idempotency_key,
            test_scenario=scenario,
        )

    # --- get / modify / cancel ----------------------------------------
    def get(self, reservation_id: str, test_scenario: Optional[str] = None) -> Dict[str, Any]:
        scenario = normalize_scenario(test_scenario)
        if scenario == SCENARIO_TECHNICAL_ERROR:
            return native_result(
                operation="get",
                status=None,
                transport_ok=False,
                reservation_id=reservation_id,
                error="TECHNICAL_ERROR",
                reason="Simulated technical error",
                test_scenario=scenario,
            )
        if scenario == SCENARIO_TIMEOUT:
            return native_result(
                operation="get",
                status=None,
                transport_ok=False,
                reservation_id=reservation_id,
                error="TIMEOUT",
                reason="Simulated timeout (immediate Native Result; no sleep)",
                test_scenario=scenario,
            )
        rec = self.store.get_reservation(reservation_id)
        if rec is None:
            return native_result(
                operation="get",
                status=None,
                transport_ok=True,
                reservation_id=reservation_id,
                error="NOT_FOUND",
                reason="Reservation not found",
                test_scenario=scenario,
            )
        return native_result(
            operation="get",
            status=rec.get("status"),
            transport_ok=True,
            reservation_id=reservation_id,
            actual=reservation_to_actual(rec),
            requested={"reservation_id": reservation_id},
            test_scenario=scenario,
        )

    def modify(
        self,
        reservation_id: str,
        fields: Dict[str, Any],
        test_scenario: Optional[str] = None,
    ) -> Dict[str, Any]:
        scenario = normalize_scenario(test_scenario)
        allowed = {"date", "time", "party_size", "seating_type", "customer_reference", "status"}
        patch = {k: v for k, v in fields.items() if k in allowed}
        requested = {"reservation_id": reservation_id, **patch}

        if scenario == SCENARIO_TECHNICAL_ERROR:
            return native_result(
                operation="modify",
                status=None,
                transport_ok=False,
                reservation_id=reservation_id,
                requested=requested,
                error="TECHNICAL_ERROR",
                reason="Simulated technical error",
                test_scenario=scenario,
            )
        if scenario == SCENARIO_TIMEOUT:
            return native_result(
                operation="modify",
                status=None,
                transport_ok=False,
                reservation_id=reservation_id,
                requested=requested,
                error="TIMEOUT",
                reason="Simulated timeout (immediate Native Result; no sleep)",
                test_scenario=scenario,
            )
        if scenario == SCENARIO_BUSINESS_REJECTED:
            return native_result(
                operation="modify",
                status=STATUS_REJECTED,
                transport_ok=True,
                reservation_id=reservation_id,
                requested=requested,
                error="BUSINESS_REJECTED",
                reason="Business policy rejected the modification",
                test_scenario=scenario,
            )

        rec = self.store.get_reservation(reservation_id)
        if rec is None:
            return native_result(
                operation="modify",
                status=None,
                transport_ok=True,
                reservation_id=reservation_id,
                requested=requested,
                error="NOT_FOUND",
                reason="Reservation not found",
                test_scenario=scenario,
            )
        if rec.get("status") == STATUS_CANCELLED:
            return native_result(
                operation="modify",
                status=STATUS_CANCELLED,
                transport_ok=True,
                reservation_id=reservation_id,
                requested=requested,
                actual=reservation_to_actual(rec),
                error="ALREADY_CANCELLED",
                reason="Cannot modify cancelled reservation",
                test_scenario=scenario,
            )
        updated = self.store.update_reservation(reservation_id, patch)
        assert updated is not None
        return native_result(
            operation="modify",
            status=updated.get("status"),
            transport_ok=True,
            reservation_id=reservation_id,
            requested=requested,
            actual=reservation_to_actual(updated),
            test_scenario=scenario,
        )

    def cancel(self, reservation_id: str, test_scenario: Optional[str] = None) -> Dict[str, Any]:
        scenario = normalize_scenario(test_scenario)
        requested = {"reservation_id": reservation_id}
        if scenario == SCENARIO_TECHNICAL_ERROR:
            return native_result(
                operation="cancel",
                status=None,
                transport_ok=False,
                reservation_id=reservation_id,
                requested=requested,
                error="TECHNICAL_ERROR",
                reason="Simulated technical error",
                test_scenario=scenario,
            )
        if scenario == SCENARIO_TIMEOUT:
            return native_result(
                operation="cancel",
                status=None,
                transport_ok=False,
                reservation_id=reservation_id,
                requested=requested,
                error="TIMEOUT",
                reason="Simulated timeout (immediate Native Result; no sleep)",
                test_scenario=scenario,
            )
        rec = self.store.get_reservation(reservation_id)
        if rec is None:
            return native_result(
                operation="cancel",
                status=None,
                transport_ok=True,
                reservation_id=reservation_id,
                requested=requested,
                error="NOT_FOUND",
                reason="Reservation not found",
                test_scenario=scenario,
            )
        updated = self.store.update_reservation(reservation_id, {"status": STATUS_CANCELLED})
        assert updated is not None
        return native_result(
            operation="cancel",
            status=STATUS_CANCELLED,
            transport_ok=True,
            reservation_id=reservation_id,
            requested=requested,
            actual=reservation_to_actual(updated),
            test_scenario=scenario,
        )
