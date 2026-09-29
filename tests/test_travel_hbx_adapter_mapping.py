"""HBX TEST booking mapper and signature — provider boundary only."""

from __future__ import annotations

import hashlib
import json
import unittest

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.connectors.providers.hbx_test_booking import (  # noqa: E402
    HBX_TEST_AUTHORIZED_BOOKING_PATH,
    HBX_TEST_AUTHORIZED_HOSTNAME,
    build_auth_headers,
    compute_x_signature,
    is_production_hbx_hostname,
    map_hbx_booking_response_to_native,
    map_stay_reserve_to_hbx_request,
)
from tests._hbx_test_helpers import (  # noqa: E402
    SENSITIVE_BOOKING_REF,
    SYNTHETIC_OPAQUE_OFFER,
    TEST_API_KEY,
    TEST_API_SECRET,
    synthetic_stay_reserve_context,
)


class HbxSignatureTestCase(unittest.TestCase):
    def test_deterministic_signature(self) -> None:
        ts = 1_700_000_000
        expected = hashlib.sha256(f"{TEST_API_KEY}{TEST_API_SECRET}{ts}".encode()).hexdigest()
        self.assertEqual(compute_x_signature(TEST_API_KEY, TEST_API_SECRET, ts), expected)
        headers = build_auth_headers(api_key=TEST_API_KEY, api_secret=TEST_API_SECRET, unix_timestamp=ts)
        self.assertEqual(headers["Api-key"], TEST_API_KEY)
        self.assertEqual(headers["X-Signature"], expected)
        self.assertNotIn(TEST_API_SECRET, json.dumps(headers))


class HbxHostnamePolicyTestCase(unittest.TestCase):
    def test_test_hostname_allowed(self) -> None:
        self.assertFalse(is_production_hbx_hostname(HBX_TEST_AUTHORIZED_HOSTNAME))

    def test_production_hostname_denied(self) -> None:
        self.assertTrue(is_production_hbx_hostname("api.hotelbeds.com"))
        self.assertTrue(is_production_hbx_hostname("api-mtls.hotelbeds.com"))


class HbxMappingTestCase(unittest.TestCase):
    def test_opaque_offer_copied_to_rate_key(self) -> None:
        mapped = map_stay_reserve_to_hbx_request(synthetic_stay_reserve_context())
        assert mapped is not None
        rate_key = mapped["rooms"][0]["rateKey"]
        self.assertEqual(rate_key, SYNTHETIC_OPAQUE_OFFER)

    def test_no_offer_in_native_payload(self) -> None:
        native = map_hbx_booking_response_to_native(
            {"booking": {"reference": SENSITIVE_BOOKING_REF, "status": "CONFIRMED"}},
        )
        assert native is not None
        blob = json.dumps(native.payload)
        self.assertNotIn(SYNTHETIC_OPAQUE_OFFER, blob)
        self.assertNotIn(SENSITIVE_BOOKING_REF, blob)
        self.assertTrue(native.payload["provider_native_result"]["booking_reference_present"])

    def test_confirmed_does_not_imply_outcome(self) -> None:
        native = map_hbx_booking_response_to_native(
            {"booking": {"reference": SENSITIVE_BOOKING_REF, "status": "CONFIRMED"}},
        )
        assert native is not None
        self.assertEqual(native.external_status, "CONFIRMED")
        self.assertFalse(native.implies_outcome_success())

    def test_booking_path_constant(self) -> None:
        self.assertEqual(HBX_TEST_AUTHORIZED_BOOKING_PATH, "/hotel-api/1.0/bookings")


if __name__ == "__main__":
    unittest.main()
