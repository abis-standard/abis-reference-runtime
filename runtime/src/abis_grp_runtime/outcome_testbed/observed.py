"""Extract observed state from Native Result — scenario labels are not semantic evidence."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from abis_grp_runtime.outcome_testbed.models import ObservedState


def extract_observed_state(native_result: Mapping[str, Any]) -> ObservedState:
    """
    Build ObservedState from Native Result actual/requested content only.

    Ignores reason, test_scenario, and other Business System test labels.
    """
    actual = dict(native_result.get("actual") or {})
    requested = dict(native_result.get("requested") or {})
    return ObservedState(
        date=actual.get("date") or requested.get("date"),
        time=actual.get("time"),
        party_size=actual.get("party_size"),
        seating_type=actual.get("seating_type"),
        status=actual.get("status") or native_result.get("status"),
        reservation_id=actual.get("reservation_id") or native_result.get("reservation_id"),
        partial=bool(actual.get("partial")),
    )


def native_result_snapshot(native_result: Mapping[str, Any]) -> dict[str, Any]:
    """Shallow reference copy for trace — does not mutate source."""
    return deepcopy(dict(native_result))
