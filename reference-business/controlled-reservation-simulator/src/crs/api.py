"""HTTP request handlers mapping to ReservationEngine (stdlib http.server)."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from crs.engine import ReservationEngine
from crs.models import native_result
from crs.scenarios import normalize_scenario

RESERVATION_PATH = re.compile(r"^/reservations/([^/]+)$")


def _scenario_from(headers: Dict[str, str], body: Optional[Dict[str, Any]]) -> Optional[str]:
    # Header takes precedence if both set inconsistently — prefer body field then header.
    # Documented: request field test_scenario OR header X-CRS-Test-Scenario (TEST ONLY).
    if body and body.get("test_scenario"):
        return normalize_scenario(str(body.get("test_scenario")))
    for k, v in headers.items():
        if k.lower() == "x-crs-test-scenario":
            return normalize_scenario(v)
    return None


def _json_body(raw: bytes) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def handle_request(
    engine: ReservationEngine,
    method: str,
    path: str,
    headers: Dict[str, str],
    raw_body: bytes = b"",
) -> Tuple[int, Dict[str, Any]]:
    """Dispatch one HTTP-shaped request. Returns (status_code, native_result_dict)."""
    parsed = urlparse(path)
    route = parsed.path
    qs = parse_qs(parsed.query)
    body = _json_body(raw_body)
    scenario = _scenario_from(headers, body)

    if method == "GET" and route == "/health":
        return 200, {
            "ok": True,
            "business_system": "abis-demo-restaurant-simulator",
            "classification": "EXTERNAL_BUSINESS_SYSTEM_TEST_DOUBLE",
            "semantic_authority": "NONE",
            "mock_only": True,
            "real_booking": "NONE",
        }

    if method == "GET" and route == "/availability":
        date = (qs.get("date") or [None])[0]
        party_size_raw = (qs.get("party_size") or ["1"])[0]
        preferred_time = (qs.get("preferred_time") or [None])[0]
        seating_type = (qs.get("seating_type") or [None])[0]
        if not date:
            return 400, native_result(
                operation="availability",
                status=None,
                transport_ok=True,
                error="BAD_REQUEST",
                reason="date is required",
                test_scenario=scenario,
            )
        try:
            party_size = int(party_size_raw)
        except (TypeError, ValueError):
            return 400, native_result(
                operation="availability",
                status=None,
                transport_ok=True,
                error="BAD_REQUEST",
                reason="party_size must be an integer",
                test_scenario=scenario,
            )
        result = engine.availability(
            date=date,
            party_size=party_size,
            preferred_time=preferred_time,
            seating_type=seating_type,
            test_scenario=scenario,
        )
        code = 200 if result.get("transport_ok") else 503
        if result.get("error") == "TIMEOUT":
            code = 504
        return code, result

    if method == "POST" and route == "/reservations":
        required = ["date", "time", "party_size", "seating_type", "customer_reference", "idempotency_key"]
        missing = [k for k in required if k not in body or body[k] in (None, "")]
        if missing:
            return 400, native_result(
                operation="reserve",
                status=None,
                transport_ok=True,
                error="BAD_REQUEST",
                reason=f"Missing fields: {', '.join(missing)}",
                test_scenario=scenario,
            )
        result = engine.reserve(
            date=str(body["date"]),
            time=str(body["time"]),
            party_size=int(body["party_size"]),
            seating_type=str(body["seating_type"]),
            customer_reference=str(body["customer_reference"]),
            idempotency_key=str(body["idempotency_key"]),
            test_scenario=scenario,
        )
        if result.get("error") == "IDEMPOTENCY_CONFLICT":
            return 409, result
        if result.get("error") == "TIMEOUT":
            return 504, result
        if not result.get("transport_ok"):
            return 503, result
        if result.get("status") in ("REJECTED",) or result.get("error"):
            return 422, result
        if result.get("idempotent_replay"):
            return 200, result
        return 201, result

    m = RESERVATION_PATH.match(route)
    if m:
        rid = m.group(1)
        if method == "GET":
            result = engine.get(rid, test_scenario=scenario)
            if result.get("error") == "NOT_FOUND":
                return 404, result
            if result.get("error") == "TIMEOUT":
                return 504, result
            if not result.get("transport_ok"):
                return 503, result
            return 200, result
        if method == "PATCH":
            fields = {k: v for k, v in body.items() if k != "test_scenario"}
            result = engine.modify(rid, fields, test_scenario=scenario)
            if result.get("error") == "NOT_FOUND":
                return 404, result
            if result.get("error") == "TIMEOUT":
                return 504, result
            if not result.get("transport_ok"):
                return 503, result
            if result.get("error"):
                return 422, result
            return 200, result
        if method == "DELETE":
            result = engine.cancel(rid, test_scenario=scenario)
            if result.get("error") == "NOT_FOUND":
                return 404, result
            if result.get("error") == "TIMEOUT":
                return 504, result
            if not result.get("transport_ok"):
                return 503, result
            return 200, result

    # TEST ONLY endpoint
    if method == "POST" and route == "/_test/scenario":
        return 200, {
            "test_only": True,
            "message": (
                "TEST ONLY: pass test_scenario in JSON body or X-CRS-Test-Scenario header "
                "on each operation call. This endpoint acknowledges scenario names only."
            ),
            "accepted_scenario": scenario or body.get("test_scenario"),
            "classification": "EXTERNAL_BUSINESS_SYSTEM_TEST_DOUBLE",
            "semantic_authority": "NONE",
        }

    return 404, native_result(
        operation="unknown",
        status=None,
        transport_ok=True,
        error="NOT_FOUND",
        reason=f"No route for {method} {route}",
        test_scenario=scenario,
    )
