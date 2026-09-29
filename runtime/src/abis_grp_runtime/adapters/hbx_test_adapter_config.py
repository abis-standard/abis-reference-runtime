"""Local-only HBX TEST mTLS adapter configuration — never Profile or public evidence."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, Optional

from abis_grp_runtime.connectors.non_production_egress import (
    EnvironmentClassification,
    TargetMode,
    _canonicalize_allowed_path,
    _normalize_hostname,
)
from abis_grp_runtime.connectors.providers.hbx_test_booking import (
    HBX_TEST_AUTHORIZED_BOOKING_PATH,
    HBX_TEST_AUTHORIZED_HOSTNAME,
    is_production_hbx_hostname,
)

PassphraseProvider = Callable[[], Optional[str]]


@dataclass(frozen=True)
class HbxTestMtlsAdapterConfig:
    """Trusted operator configuration for HBX TEST mTLS booking (non-serialized)."""

    enabled: bool
    adapter_id: str
    allowlist_id: str
    target_authorization_id: str
    authorized_hostname: str
    authorized_port: int
    allowed_paths: tuple[str, ...]
    environment_classification: EnvironmentClassification
    timeout_seconds: float
    max_response_bytes: int
    max_request_body_bytes: int
    client_certificate_path: str
    encrypted_private_key_path: str
    api_key_env_var: str
    api_secret_env_var: str
    private_key_passphrase_env_var: str | None = None
    passphrase_provider: PassphraseProvider | None = None
    mapping_version: str = "1"

    @property
    def target_mode(self) -> TargetMode:
        return TargetMode.REMOTE_AUTHORIZED

    def structurally_valid(self) -> bool:
        if not self.enabled:
            return False
        if not self.adapter_id or not self.allowlist_id or not self.target_authorization_id:
            return False
        if not self.allowed_paths:
            return False
        if not self.environment_classification.potentially_allowed():
            return False
        try:
            host = _normalize_hostname(self.authorized_hostname)
        except ValueError:
            return False
        if host != HBX_TEST_AUTHORIZED_HOSTNAME:
            return False
        if is_production_hbx_hostname(host):
            return False
        if self.authorized_port <= 0 or self.authorized_port > 65535:
            return False
        for path in self.allowed_paths:
            if _canonicalize_allowed_path(path) is None:
                return False
        if HBX_TEST_AUTHORIZED_BOOKING_PATH not in self.allowed_paths:
            return False
        if not self.client_certificate_path or not self.encrypted_private_key_path:
            return False
        if not self.api_key_env_var or not self.api_secret_env_var:
            return False
        return True

    def passphrase_available(self) -> bool:
        if self.passphrase_provider is not None:
            try:
                value = self.passphrase_provider()
            except Exception:
                return False
            return value is not None and str(value) != ""
        if self.private_key_passphrase_env_var:
            value = os.environ.get(self.private_key_passphrase_env_var)
            return bool(value and value.strip())
        return False

    def api_credentials_available(self) -> bool:
        key = os.environ.get(self.api_key_env_var, "").strip()
        secret = os.environ.get(self.api_secret_env_var, "").strip()
        return bool(key and secret)

    def certificate_paths_available(self) -> bool:
        return os.path.isfile(self.client_certificate_path) and os.path.isfile(
            self.encrypted_private_key_path
        )

    def fully_configured(self) -> bool:
        return (
            self.structurally_valid()
            and self.passphrase_available()
            and self.api_credentials_available()
            and self.certificate_paths_available()
        )
