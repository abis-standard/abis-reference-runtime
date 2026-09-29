"""HBX TEST booking mapper and auth — provider boundary only."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from abis_grp_runtime.native_result import NativeResultEnvelope

HBX_TEST_AUTHORIZED_HOSTNAME = "api-mtls.test.hotelbeds.com"
HBX_TEST_AUTHORIZED_BOOKING_PATH = "/hotel-api/1.0/bookings"

_HBX_PRODUCTION_HOSTNAMES = frozenset(
    {
        "api.hotelbeds.com",
        "api-mtls.hotelbeds.com",
        "www.hotelbeds.com",
    }
)

CONNECTOR_ID = "authorized-mtls-sandbox-hbx-test-travel"
PROVIDER_ENVIRONMENT = "TEST"


def is_production_hbx_hostname(hostname: str) -> bool:
    try:
        normalized = hostname.strip().lower().rstrip(".")
    except AttributeError:
        return True
    return normalized in _HBX_PRODUCTION_HOSTNAMES


def compute_x_signature(api_key: str, api_secret: str, unix_timestamp: int) -> str:
    material = f"{api_key}{api_secret}{unix_timestamp}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def build_auth_headers(
    *,
    api_key: str,
    api_secret: str,
    unix_timestamp: int,
) -> dict[str, str]:
    signature = compute_x_signature(api_key, api_secret, unix_timestamp)
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Api-key": api_key,
        "X-Signature": signature,
    }


def map_stay_reserve_to_hbx_request(ctx: Mapping[str, Any]) -> dict[str, Any] | None:
    """Provider-neutral stay_reserve context → HBX-style booking JSON (opaque offer copy)."""
    try:
        holder = dict(ctx.get("holder") or {})
        guests = list(ctx.get("guests") or [])
        offer_ref = str(ctx.get("selected_offer_reference") or "").strip()
        client_ref = str(ctx.get("client_reference") or "").strip()
        if not offer_ref or not client_ref:
            return None
        paxes = []
        for guest in guests:
            if not isinstance(guest, dict):
                return None
            paxes.append(
                {
                    "roomId": int(guest.get("room_id", 1)),
                    "type": str(guest.get("type", "AD")),
                    "name": str(guest.get("name", "Synthetic")),
                    "surname": str(guest.get("surname", "Guest")),
                }
            )
        return {
            "holder": {
                "name": str(holder.get("name", "Synthetic")),
                "surname": str(holder.get("surname", "Holder")),
            },
            "rooms": [
                {
                    "rateKey": offer_ref,
                    "paxes": paxes,
                }
            ],
            "clientReference": client_ref,
        }
    except (TypeError, ValueError):
        return None


def map_hbx_booking_response_to_native(
    data: Mapping[str, Any],
    *,
    timing_ms: int | None = None,
) -> NativeResultEnvelope | None:
    if not isinstance(data, dict):
        return None
    booking = data.get("booking")
    if not isinstance(booking, dict):
        return None
    reference = booking.get("reference")
    status = booking.get("status")
    if not reference or not status:
        return None
    status_text = str(status)
    return NativeResultEnvelope(
        technical_status="TRANSPORT_OK",
        external_status=status_text,
        external_identifier=str(reference),
        source=CONNECTOR_ID,
        timing_ms=timing_ms,
        payload={
            "operation": "stay_reserve",
            "provider_native_result": {
                "classification": "AUTHORIZED_NON_PRODUCTION_PROVIDER_NATIVE",
                "provider_environment": PROVIDER_ENVIRONMENT,
                "semantic_authority": "NONE",
                "booking_status_observed": status_text,
                "booking_reference_present": True,
            },
        },
    )


def parse_hbx_json_response(body: bytes) -> dict[str, Any] | None:
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None
