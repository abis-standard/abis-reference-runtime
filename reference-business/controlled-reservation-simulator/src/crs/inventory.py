"""Deterministic seating inventory template.

Template date 2026-09-12; any date clones the same slot template.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

from crs.models import SEATING_PRIVATE_ROOM, SEATING_TABLE

# Slot template for private_room (and mirrored availability semantics for TABLE).
# capacity 0 or UNAVAILABLE => not bookable.
TEMPLATE_SLOTS: List[Dict[str, Any]] = [
    {"time": "18:00", "capacity": 4, "seating_type": SEATING_PRIVATE_ROOM, "availability": "AVAILABLE"},
    {"time": "18:30", "capacity": 2, "seating_type": SEATING_PRIVATE_ROOM, "availability": "UNAVAILABLE"},
    {"time": "19:00", "capacity": 4, "seating_type": SEATING_PRIVATE_ROOM, "availability": "UNAVAILABLE"},
    {"time": "19:30", "capacity": 0, "seating_type": SEATING_PRIVATE_ROOM, "availability": "UNAVAILABLE"},
    {"time": "20:00", "capacity": 8, "seating_type": SEATING_PRIVATE_ROOM, "availability": "AVAILABLE"},
]

# TABLE seats: same times; available when private_room is AVAILABLE or as fallback
# for TECHNICAL_SUCCESS_BUSINESS_MISMATCH golden (19:30 TABLE).
TABLE_TEMPLATE_SLOTS: List[Dict[str, Any]] = [
    {"time": "18:00", "capacity": 4, "seating_type": SEATING_TABLE, "availability": "AVAILABLE"},
    {"time": "18:30", "capacity": 2, "seating_type": SEATING_TABLE, "availability": "AVAILABLE"},
    {"time": "19:00", "capacity": 4, "seating_type": SEATING_TABLE, "availability": "AVAILABLE"},
    {"time": "19:30", "capacity": 4, "seating_type": SEATING_TABLE, "availability": "AVAILABLE"},
    {"time": "20:00", "capacity": 8, "seating_type": SEATING_TABLE, "availability": "AVAILABLE"},
]


def slots_for_date(date: str) -> List[Dict[str, Any]]:
    """Clone template slots for any date (deterministic)."""
    out: List[Dict[str, Any]] = []
    for s in TEMPLATE_SLOTS:
        row = deepcopy(s)
        row["date"] = date
        out.append(row)
    for s in TABLE_TEMPLATE_SLOTS:
        row = deepcopy(s)
        row["date"] = date
        out.append(row)
    return out


def find_slot(
    date: str,
    time: str,
    seating_type: str,
) -> Optional[Dict[str, Any]]:
    for s in slots_for_date(date):
        if s["time"] == time and s["seating_type"] == seating_type:
            return s
    return None


def is_slot_available(slot: Optional[Dict[str, Any]], party_size: int) -> bool:
    if not slot:
        return False
    if slot.get("availability") != "AVAILABLE":
        return False
    cap = int(slot.get("capacity") or 0)
    return cap >= int(party_size)


def query_availability(
    date: str,
    party_size: int,
    preferred_time: Optional[str] = None,
    seating_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return bookable slots matching filters."""
    results: List[Dict[str, Any]] = []
    for s in slots_for_date(date):
        if seating_type and s["seating_type"] != seating_type:
            continue
        if preferred_time and s["time"] != preferred_time:
            continue
        if not is_slot_available(s, party_size):
            continue
        results.append(
            {
                "date": date,
                "time": s["time"],
                "seating_type": s["seating_type"],
                "capacity": s["capacity"],
                "availability": "AVAILABLE",
            }
        )
    return results
