"""Local-only HTTP adapter configuration — never serialized to Profile or public evidence."""

from __future__ import annotations

import os
from dataclasses import dataclass

from abis_grp_runtime.connectors.non_production_egress import EnvironmentClassification


@dataclass(frozen=True)
class RestaurantHttpAdapterConfig:
    """Trusted local configuration for restaurant authorized non-production HTTP adapter."""

    enabled: bool
    adapter_id: str
    allowlist_id: str
    base_url: str
    allowed_paths: tuple[str, ...]
    environment_classification: EnvironmentClassification
    timeout_seconds: float
    max_response_bytes: int
    mapping_version: str
    credential_env_var: str | None = None

    def structurally_valid(self) -> bool:
        if not self.enabled:
            return False
        if not self.adapter_id or not self.allowlist_id:
            return False
        if not self.base_url or not self.allowed_paths:
            return False
        if not self.environment_classification.potentially_allowed():
            return False
        return True

    def credential_available(self) -> bool:
        if not self.credential_env_var:
            return True
        value = os.environ.get(self.credential_env_var)
        return bool(value and value.strip())


def load_restaurant_http_adapter_config_from_env() -> RestaurantHttpAdapterConfig | None:
    enabled_raw = os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_ENABLED", "").strip().lower()
    enabled = enabled_raw in ("1", "true", "yes", "on")
    if not enabled:
        return None

    base_url = os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_BASE_URL", "").strip()
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
        base_url=base_url,
        allowed_paths=paths,
        environment_classification=env_class,
        timeout_seconds=float(os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_TIMEOUT", "5")),
        max_response_bytes=int(os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_MAX_BYTES", "65536")),
        mapping_version=os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_MAPPING_VERSION", "1").strip(),
        credential_env_var=os.environ.get("ABIS_RESTAURANT_HTTP_ADAPTER_CREDENTIAL_ENV") or None,
    )
