"""Authorized non-production mTLS sandbox connector — fail-closed egress + injectable transport."""

from __future__ import annotations

import json
import os
import time
from http.client import HTTPException
from typing import Any, Callable, Mapping

from abis_grp_runtime.adapters.hbx_test_adapter_config import HbxTestMtlsAdapterConfig
from abis_grp_runtime.connectors.bound_https_transport import https_post_json as bound_https_post_json
from abis_grp_runtime.connectors.mtls_ssl_context import MtlsConfigurationError, build_client_mtls_context
from abis_grp_runtime.connectors.non_production_egress import (
    EgressDecision,
    NonProductionEgressPolicy,
    ValidatedDestination,
)
from abis_grp_runtime.connectors.providers.hbx_test_booking import (
    CONNECTOR_ID,
    HBX_TEST_AUTHORIZED_BOOKING_PATH,
    PROVIDER_ENVIRONMENT,
    build_auth_headers,
    map_hbx_booking_response_to_native,
    map_stay_reserve_to_hbx_request,
    parse_hbx_json_response,
)
from abis_grp_runtime.connector import BusinessConnectorPort
from abis_grp_runtime.native_result import NativeResultEnvelope

CONNECTOR_KIND = "authorized_mtls_sandbox"

HttpsPostFn = Callable[
    [ValidatedDestination, str, Mapping[str, str], bytes, float, int, Any],
    tuple[int, bytes, str],
]


class AuthorizedMtlsSandboxConnector(BusinessConnectorPort):
    """
    HBX TEST mTLS booking boundary for travel/stay_reserve.

    Network I/O is injectable for deterministic tests (C2: no live HBX).
    """

    connector_id = CONNECTOR_ID

    def __init__(
        self,
        config: HbxTestMtlsAdapterConfig,
        *,
        policy: NonProductionEgressPolicy | None = None,
        https_post: HttpsPostFn | None = None,
        unix_timestamp: int | None = None,
    ) -> None:
        self._config = config
        self._https_post = https_post or self._default_https_post
        self._unix_timestamp = unix_timestamp
        self._policy = policy or NonProductionEgressPolicy(
            allowlist_id=config.allowlist_id,
            target_mode=config.target_mode,
            authorized_hostname=config.authorized_hostname,
            authorized_port=config.authorized_port,
            allowed_paths=config.allowed_paths,
            environment_classification=config.environment_classification,
            target_authorization_id=config.target_authorization_id,
        )
        self._last_metadata: dict[str, Any] = {}

    @staticmethod
    def _default_https_post(
        destination: ValidatedDestination,
        path: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout: float,
        max_response_bytes: int,
        ssl_context: Any,
    ) -> tuple[int, bytes, str]:
        return bound_https_post_json(
            destination,
            path=path,
            headers=headers,
            body=body,
            timeout=timeout,
            max_response_bytes=max_response_bytes,
            ssl_context=ssl_context,
        )

    def consume_execution_metadata(self) -> dict[str, Any]:
        return dict(self._last_metadata)

    def _set_metadata(
        self,
        *,
        external_request_attempted: bool,
        external_response_received: bool,
        egress_decision: str,
        egress_reason: str,
        provider_native_status: str | None = None,
        destination: ValidatedDestination | None = None,
        tls_verified: bool = False,
    ) -> None:
        egress: dict[str, Any] = {
            "decision": egress_decision,
            "allowlist_id": self._config.allowlist_id,
            "reason": egress_reason,
            "target_mode": self._config.target_mode.value,
        }
        meta: dict[str, Any] = {
            "connector": {"id": self._config.adapter_id, "kind": CONNECTOR_KIND},
            "mapping_version": self._config.mapping_version,
            "environment_classification": self._config.environment_classification.value,
            "target_authorization_id": self._config.target_authorization_id,
            "provider_environment": PROVIDER_ENVIRONMENT,
            "egress": egress,
            "external_request_attempted": external_request_attempted,
            "external_response_received": external_response_received,
            "business_outcome": "NOT_EVALUATED",
        }
        if provider_native_status:
            meta["provider_native_status"] = provider_native_status
        if destination is not None:
            meta["transport"] = {"tls": "VERIFIED" if tls_verified else "NOT_ATTEMPTED", "mtls": "CLIENT_CERT"}
        self._last_metadata = meta

    def _failure(
        self,
        code: str,
        message: str,
        *,
        attempted: bool = False,
        received: bool = False,
        egress_decision: str = "DENY",
        egress_reason: str = "",
        destination: ValidatedDestination | None = None,
    ) -> NativeResultEnvelope:
        self._set_metadata(
            external_request_attempted=attempted,
            external_response_received=received,
            egress_decision=egress_decision,
            egress_reason=egress_reason or message,
            destination=destination,
        )
        return NativeResultEnvelope(
            technical_status="TRANSPORT_FAILED",
            external_status=None,
            source=self.connector_id,
            error={"code": code, "message": message},
            payload={"operation": "stay_reserve"},
        )

    def _resolve_timestamp(self) -> int:
        if self._unix_timestamp is not None:
            return int(self._unix_timestamp)
        return int(time.time())

    def _build_ssl_context(self) -> Any:
        return build_client_mtls_context(
            certificate_path=self._config.client_certificate_path,
            private_key_path=self._config.encrypted_private_key_path,
            passphrase_provider=self._config.passphrase_provider
            or self._env_passphrase_provider(),
        )

    def _env_passphrase_provider(self) -> Callable[[], str | None]:
        env_var = self._config.private_key_passphrase_env_var

        def _provider() -> str | None:
            if not env_var:
                return None
            value = os.environ.get(env_var)
            return value.strip() if value else None

        return _provider

    def execute(self, operation: str, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        op = operation.strip().lower()
        if op != "stay_reserve":
            return self._failure("UNSUPPORTED_OPERATION", f"unsupported operation: {operation}")

        if not self._config.structurally_valid():
            return self._failure("ADAPTER_NOT_CONFIGURED", "adapter configuration invalid or disabled")

        if not self._config.api_credentials_available():
            return self._failure("AUTH_CONFIG_MISSING", "API credentials not available")

        if not self._config.passphrase_available():
            return self._failure("MTLS_CONFIG_MISSING", "private key passphrase not available")

        booking_path = HBX_TEST_AUTHORIZED_BOOKING_PATH
        if booking_path not in self._config.allowed_paths:
            return self._failure(
                "EGRESS_DENIED",
                "authorized booking path not in allowlist",
                egress_decision="DENY",
                egress_reason="authorized booking path not in allowlist",
            )
        destination, verdict = self._policy.resolve_validated_destination(booking_path)
        if verdict.decision is EgressDecision.DENY or destination is None:
            return self._failure(
                "EGRESS_DENIED",
                verdict.reason,
                egress_decision="DENY",
                egress_reason=verdict.reason,
            )

        body_obj = map_stay_reserve_to_hbx_request(operation_context)
        if body_obj is None:
            return self._failure(
                "MAPPING_FAILURE",
                "structured input mapping failed",
                egress_decision="ALLOW",
                egress_reason=verdict.reason,
                destination=destination,
            )

        payload = json.dumps(body_obj).encode("utf-8")
        if len(payload) > self._config.max_request_body_bytes:
            return self._failure(
                "REQUEST_TOO_LARGE",
                "request body exceeds size limit",
                egress_decision="ALLOW",
                egress_reason=verdict.reason,
                destination=destination,
            )

        api_key = os.environ.get(self._config.api_key_env_var, "").strip()
        api_secret = os.environ.get(self._config.api_secret_env_var, "").strip()
        ts = self._resolve_timestamp()
        headers = build_auth_headers(api_key=api_key, api_secret=api_secret, unix_timestamp=ts)

        started = time.monotonic()
        try:
            ssl_context = self._build_ssl_context()
        except MtlsConfigurationError as exc:
            return self._failure(
                "MTLS_CONFIG_ERROR",
                str(exc),
                egress_decision="ALLOW",
                egress_reason=verdict.reason,
                destination=destination,
            )

        try:
            status, response_bytes, content_type = self._https_post(
                destination,
                destination.request_path,
                headers,
                payload,
                self._config.timeout_seconds,
                self._config.max_response_bytes,
                ssl_context,
            )
        except TimeoutError:
            return self._failure(
                "NETWORK_TIMEOUT",
                "HTTPS request timed out",
                attempted=True,
                egress_decision="ALLOW",
                egress_reason=verdict.reason,
                destination=destination,
            )
        except (HTTPException, OSError):
            return self._failure(
                "NETWORK_ERROR",
                "transport failure",
                attempted=True,
                egress_decision="ALLOW",
                egress_reason=verdict.reason,
                destination=destination,
            )

        timing_ms = int((time.monotonic() - started) * 1000)

        if status is None:
            return self._failure(
                "NETWORK_ERROR",
                "no HTTP response",
                attempted=True,
                egress_decision="ALLOW",
                egress_reason=verdict.reason,
                destination=destination,
            )

        if status in (301, 302, 303, 307, 308):
            return self._failure(
                "REDIRECT_DENIED",
                "redirect response not permitted",
                attempted=True,
                received=True,
                egress_decision="ALLOW",
                egress_reason=verdict.reason,
                destination=destination,
            )

        if status == 401 or status == 403:
            return self._failure(
                "AUTH_REJECTED",
                f"provider HTTP {status}",
                attempted=True,
                received=True,
                egress_decision="ALLOW",
                egress_reason=verdict.reason,
                destination=destination,
            )

        if 400 <= status < 500:
            return self._failure(
                "HTTP_4XX",
                f"external HTTP {status}",
                attempted=True,
                received=True,
                egress_decision="ALLOW",
                egress_reason=verdict.reason,
                destination=destination,
            )
        if status >= 500:
            return self._failure(
                "HTTP_5XX",
                f"external HTTP {status}",
                attempted=True,
                received=True,
                egress_decision="ALLOW",
                egress_reason=verdict.reason,
                destination=destination,
            )

        if not content_type.lower().startswith("application/json"):
            return self._failure(
                "MALFORMED_EXTERNAL_RESPONSE",
                "unexpected Content-Type",
                attempted=True,
                received=True,
                egress_decision="ALLOW",
                egress_reason=verdict.reason,
                destination=destination,
            )

        if len(response_bytes) > self._config.max_response_bytes:
            return self._failure(
                "MALFORMED_EXTERNAL_RESPONSE",
                "response exceeds size limit",
                attempted=True,
                received=True,
                egress_decision="ALLOW",
                egress_reason=verdict.reason,
                destination=destination,
            )

        parsed = parse_hbx_json_response(response_bytes)
        if parsed is None:
            return self._failure(
                "MALFORMED_EXTERNAL_RESPONSE",
                "invalid JSON response",
                attempted=True,
                received=True,
                egress_decision="ALLOW",
                egress_reason=verdict.reason,
                destination=destination,
            )

        native = map_hbx_booking_response_to_native(parsed, timing_ms=timing_ms)
        if native is None:
            return self._failure(
                "MALFORMED_EXTERNAL_RESPONSE",
                "response mapping failed",
                attempted=True,
                received=True,
                egress_decision="ALLOW",
                egress_reason=verdict.reason,
                destination=destination,
            )

        self._set_metadata(
            external_request_attempted=True,
            external_response_received=True,
            egress_decision="ALLOW",
            egress_reason=verdict.reason,
            provider_native_status=native.external_status,
            destination=destination,
            tls_verified=True,
        )
        return native
