"""Local-only HTTP adapter configuration — never serialized to Profile or public evidence."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from abis_grp_runtime.connectors.non_production_egress import (
    EnvironmentClassification,
    TargetMode,
    _canonicalize_allowed_path,
    _normalize_hostname,
)


@dataclass(frozen=True)
class RestaurantHttpAdapterConfig:
    """Trusted local configuration for restaurant authorized non-production HTTP adapter."""

    enabled: bool
    adapter_id: str
    allowlist_id: str
    target_mode: TargetMode
    target_authorization_id: str
    authorized_hostname: str
    authorized_port: int
    allowed_paths: tuple[str, ...]
    environment_classification: EnvironmentClassification
    timeout_seconds: float
    max_response_bytes: int
    max_request_body_bytes: int
    mapping_version: str
    base_url: str | None = None
    credential_env_var: str | None = None

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
            _normalize_hostname(self.authorized_hostname)
        except ValueError:
            return False
        if "*" in self.authorized_hostname:
            return False
        for path in self.allowed_paths:
            if _canonicalize_allowed_path(path) is None:
                return False
        if self.target_mode is TargetMode.REMOTE_AUTHORIZED:
            if self.authorized_port <= 0 or self.authorized_port > 65535:
                return False
            if not self.credential_env_var:
                return False
        if self.base_url:
            try:
                parsed = urlparse(self.base_url)
                if not parsed.scheme or not parsed.hostname:
                    return False
            except ValueError:
                return False
        return True

    def remote_credential_required(self) -> bool:
        return self.target_mode is TargetMode.REMOTE_AUTHORIZED

    def credential_available(self) -> bool:
        if self.remote_credential_required():
            if not self.credential_env_var:
                return False
            value = os.environ.get(self.credential_env_var)
            return bool(value and value.strip())
        if not self.credential_env_var:
            return True
        value = os.environ.get(self.credential_env_var)
        return bool(value and value.strip())


def _infer_target_mode_from_base_url(base_url: str) -> TargetMode | None:
    parsed = urlparse(base_url.strip())
    host = (parsed.hostname or "").lower()
    if not host:
        return None
    if host in {"127.0.0.1", "localhost", "::1"}:
        return TargetMode.LOCALHOST_MOCK
    if parsed.scheme == "https":
        return TargetMode.REMOTE_AUTHORIZED
    return None


def load_restaurant_http_adapter_config_from_env() -> RestaurantHttpAdapterConfig | None:
    enabled_raw = os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_ENABLED", "").strip().lower()
    enabled = enabled_raw in ("1", "true", "yes", "on")
    if not enabled:
        return None

    base_url = os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_BASE_URL", "").strip() or None
    mode_raw = os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_TARGET_MODE", "").strip().upper()
    if mode_raw:
        try:
            target_mode = TargetMode(mode_raw)
        except ValueError:
            target_mode = TargetMode.LOCALHOST_MOCK
    elif base_url:
        inferred = _infer_target_mode_from_base_url(base_url)
        target_mode = inferred or TargetMode.LOCALHOST_MOCK
    else:
        target_mode = TargetMode.LOCALHOST_MOCK

    hostname = os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_AUTHORIZED_HOSTNAME", "").strip()
    if not hostname and base_url:
        hostname = urlparse(base_url).hostname or ""
    if not hostname:
        hostname = "127.0.0.1" if target_mode is TargetMode.LOCALHOST_MOCK else ""

    port_raw = os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_AUTHORIZED_PORT", "").strip()
    if port_raw:
        authorized_port = int(port_raw)
    elif base_url and urlparse(base_url).port:
        authorized_port = int(urlparse(base_url).port)
    elif target_mode is TargetMode.REMOTE_AUTHORIZED:
        authorized_port = 443
    else:
        authorized_port = 80

    path = os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_PATH", "/sandbox/v1/reservations").strip()
    paths = (path,) if path else ()

    env_class = EnvironmentClassification.parse(
        os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_ENV", "MOCK")
    )

    return RestaurantHttpAdapterConfig(
        enabled=True,
        adapter_id=os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_ID", "restaurant-http-sandbox").strip(),
        allowlist_id=os.environ.get(
            "ABIS_RESTAURANT_HTTP_ADAPTER_ALLOWLIST_ID", "local-mock-restaurant-v1"
        ).strip(),
        target_mode=target_mode,
        target_authorization_id=os.environ.get(
            "ABIS_RESTAURANT_HTTP_ADAPTER_TARGET_AUTHORIZATION_ID",
            os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_ALLOWLIST_ID", "local-mock-restaurant-v1"),
        ).strip(),
        authorized_hostname=hostname,
        authorized_port=authorized_port,
        base_url=base_url,
        allowed_paths=paths,
        environment_classification=env_class,
        timeout_seconds=float(os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_TIMEOUT", "5")),
        max_response_bytes=int(os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_MAX_BYTES", "65536")),
        max_request_body_bytes=int(
            os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_MAX_REQUEST_BYTES", "16384")
        ),
        mapping_version=os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_MAPPING_VERSION", "1").strip(),
        credential_env_var=os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_CREDENTIAL_ENV") or None,
    )
