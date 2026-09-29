"""Synthetic HBX TEST fixtures for C2 — no real credentials or network."""

from __future__ import annotations

import json
import os
from pathlib import Path

from abis_grp_runtime.adapters.hbx_test_adapter_config import HbxTestMtlsAdapterConfig
from abis_grp_runtime.connectors.non_production_egress import EnvironmentClassification
from abis_grp_runtime.connectors.providers.hbx_test_booking import (
    HBX_TEST_AUTHORIZED_BOOKING_PATH,
    HBX_TEST_AUTHORIZED_HOSTNAME,
)

SYNTHETIC_OPAQUE_OFFER = "OPAQUE-SYNTHETIC-OFFER-FIXTURE-C2"
SENSITIVE_BOOKING_REF = "SENSITIVE-SYNTHETIC-BOOKING-REFERENCE"
TEST_API_KEY = "TEST_API_KEY"
TEST_API_SECRET = "TEST_API_SECRET"
TEST_PASSPHRASE = "TEST-PASSPHRASE-SYNTHETIC"


def write_synthetic_pem_files(directory: str) -> tuple[str, str]:
    cert = Path(directory) / "synthetic_client.pem"
    key = Path(directory) / "synthetic_client_encrypted.key"
    cert.write_text("-----BEGIN CERTIFICATE-----\nSYNTHETIC-CERT-PLACEHOLDER\n-----END CERTIFICATE-----\n")
    key.write_text("-----BEGIN ENCRYPTED PRIVATE KEY-----\nSYNTHETIC-KEY-PLACEHOLDER\n-----END ENCRYPTED PRIVATE KEY-----\n")
    return str(cert), str(key)


def synthetic_hbx_config(
    directory: str,
    *,
    hostname: str = HBX_TEST_AUTHORIZED_HOSTNAME,
    allowed_paths: tuple[str, ...] = (HBX_TEST_AUTHORIZED_BOOKING_PATH,),
) -> HbxTestMtlsAdapterConfig:
    cert_path, key_path = write_synthetic_pem_files(directory)
    os.environ["ABIS_HBX_TEST_API_KEY"] = TEST_API_KEY
    os.environ["ABIS_HBX_TEST_API_SECRET"] = TEST_API_SECRET
    return HbxTestMtlsAdapterConfig(
        enabled=True,
        adapter_id="hbx-test-travel-mtls",
        allowlist_id="hbx-test-mtls-allowlist",
        target_authorization_id="hbx-test-mtls-authz",
        authorized_hostname=hostname,
        authorized_port=443,
        allowed_paths=allowed_paths,
        environment_classification=EnvironmentClassification.SANDBOX,
        timeout_seconds=5.0,
        max_response_bytes=65536,
        max_request_body_bytes=65536,
        client_certificate_path=cert_path,
        encrypted_private_key_path=key_path,
        api_key_env_var="ABIS_HBX_TEST_API_KEY",
        api_secret_env_var="ABIS_HBX_TEST_API_SECRET",
        passphrase_provider=lambda: TEST_PASSPHRASE,
    )


def synthetic_stay_reserve_context(**overrides: object) -> dict:
    payload = {
        "stay": {"check_in": "2026-11-01", "check_out": "2026-11-02"},
        "occupancy": {"rooms": 1, "adults": 1, "children": 0},
        "holder": {"name": "Synthetic", "surname": "Holder"},
        "guests": [{"room_id": 1, "type": "AD", "name": "Synthetic", "surname": "Guest"}],
        "selected_offer_reference": SYNTHETIC_OPAQUE_OFFER,
        "client_reference": "ABIS-TRAVEL-C2",
    }
    payload.update(overrides)
    return payload


def load_hbx_fixture(name: str) -> dict:
    root = Path(__file__).resolve().parents[1]
    path = root / "fixtures" / "hbx" / name
    return json.loads(path.read_text(encoding="utf-8"))
