"""External demo gateway configuration — env-driven, no committed secrets."""

from __future__ import annotations

import os
from dataclasses import dataclass


ALLOWED_GATEWAY_MODES = frozenset({"EXTERNAL_TEST", "EXTERNAL_PRESENTATION"})
ALLOWED_VERTICALS_M206B = frozenset({"restaurant"})
ALLOWED_OPERATIONS = frozenset({"reserve"})
ALLOWED_EXECUTION_CLASSES = frozenset({"CONTROLLED_SIMULATOR"})


@dataclass(frozen=True)
class GatewayConfig:
    host: str = "127.0.0.1"
    port: int = 9080
    mode: str = "EXTERNAL_TEST"
    bearer_token: str | None = None
    max_body_bytes: int = 65536
    requests_per_minute: int = 60
    max_concurrent: int = 8
    request_timeout_seconds: float = 30.0
    tls_cert_file: str | None = None
    tls_key_file: str | None = None
    evidence_log_path: str | None = None

    @classmethod
    def from_env(cls) -> "GatewayConfig":
        mode = os.environ.get("ABIS_GATEWAY_MODE", "EXTERNAL_TEST").strip().upper()
        token = os.environ.get("ABIS_DEMO_GATEWAY_TOKEN") or os.environ.get("GROK_E2E_SHARED_SECRET")
        return cls(
            host=os.environ.get("ABIS_DEMO_GATEWAY_HOST", "127.0.0.1").strip(),
            port=int(os.environ.get("ABIS_DEMO_GATEWAY_PORT", "9080")),
            mode=mode,
            bearer_token=token.strip() if token else None,
            max_body_bytes=int(os.environ.get("ABIS_DEMO_GATEWAY_MAX_BODY", "65536")),
            requests_per_minute=int(os.environ.get("ABIS_DEMO_GATEWAY_RPM", "60")),
            max_concurrent=int(os.environ.get("ABIS_DEMO_GATEWAY_MAX_CONCURRENT", "8")),
            request_timeout_seconds=float(os.environ.get("ABIS_DEMO_GATEWAY_TIMEOUT", "30")),
            tls_cert_file=os.environ.get("ABIS_DEMO_GATEWAY_TLS_CERT"),
            tls_key_file=os.environ.get("ABIS_DEMO_GATEWAY_TLS_KEY"),
            evidence_log_path=os.environ.get("ABIS_DEMO_GATEWAY_EVIDENCE_LOG"),
        )

    def validate_startup(self) -> None:
        if self.mode not in ALLOWED_GATEWAY_MODES:
            raise ValueError(f"unsupported ABIS_GATEWAY_MODE: {self.mode}")
        if not self.bearer_token:
            raise ValueError("ABIS_DEMO_GATEWAY_TOKEN is required and must not be empty")
        if self.host not in ("127.0.0.1", "localhost"):
            raise ValueError("gateway must bind to localhost only unless exposed via external tunnel/proxy")
        if self.tls_cert_file or self.tls_key_file:
            if not (self.tls_cert_file and self.tls_key_file):
                raise ValueError("both ABIS_DEMO_GATEWAY_TLS_CERT and ABIS_DEMO_GATEWAY_TLS_KEY required for TLS")
