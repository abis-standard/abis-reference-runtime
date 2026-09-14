"""Controlled Reservation Simulator (CRS) — EXTERNAL BUSINESS SYSTEM TEST DOUBLE.

MOCK-ONLY. REAL_BOOKING NONE. semantic_authority = NONE.
Native Result ≠ ABIS Outcome. Never emits ABIS verdict labels.
"""

__version__ = "0.1.0"
__all__ = [
    "BUSINESS_SYSTEM_ID",
    "RESTAURANT_NAME",
    "ReservationEngine",
    "JsonFileStore",
]

BUSINESS_SYSTEM_ID = "abis-demo-restaurant-simulator"
RESTAURANT_NAME = "ABIS Demo Restaurant"

from crs.engine import ReservationEngine  # noqa: E402
from crs.store import JsonFileStore  # noqa: E402
