"""Authorized non-production HTTP sandbox connector — BusinessConnectorPort implementation."""

from __future__ import annotations

import json
import os
import time
from http.client import HTTPException
from typing import Any, Mapping

from abis_grp_runtime.adapters.http_adapter_config import RestaurantHttpAdapterConfig
from abis_grp_runtime.connectors.bound_http_transport import http_post_json as bound_http_post_json
from abis_grp_runtime.connectors.bound_https_transport import https_post_json as bound_https_post_json
from abis_grp_runtime.connectors.non_production_egress import (
    EgressDecision,
    NonProductionEgressPolicy,
    TargetMode,
    ValidatedDestination,
)
from abis_grp_runtime.connector import BusinessConnectorPort
from abis_grp_runtime.native_result import NativeResultEnvelope

CONNECTOR_KIND = "authorized_http_sandbox"
MAPPING_VERSION_DEFAULT = "1"


class AuthorizedHttpSandboxConnector(BusinessConnectorPort):
    """
    Restaurant reserve → authorized non-production HTTP(S) boundary.

    Control metadata is exposed via consume_execution_metadata(), not NativeResult payload.
    """

    connector_id = "authorized-http-sandbox-restaurant"

    def __init__(
        self,
        config: RestaurantHttpAdapterConfig,
        *,
        policy: NonProductionEgressPolicy | None = None,
        ssl_context_factory: Any | None = None,
    ) -> None:
        self._config = config
        self._ssl_context_factory = ssl_context_factory
        self._policy = policy or NonProductionEgressPolicy(
            allowlist_id=config.allowlist_id,
            target_mode=config.target_mode,
            authorized_hostname=config.authorized_hostname,
            authorized_port=config.authorized_port,
            allowed_paths=config.allowed_paths,
            environment_classification=config.environment_classification,
            target_authorization_id=config.target_authorization_id,
            base_url=config.base_url,
        )
        self._last_metadata: dict[str, Any] = {}

    def consume_execution_metadata(self) -> dict[str, Any]:
        return dict(self._last_metadata)

    def _set_metadata(
        self,
        *,
        external_request_attempted: bool,
        external_response_received: bool,
        egress_decision: str,
        egress_reason: str,
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
            "connector": {
                "id": self._config.adapter_id,
                "kind": CONNECTOR_KIND,
            },
            "mapping_version": self._config.mapping_version,
            "environment_classification": self._config.environment_classification.value,
            "target_authorization_id": self._config.target_authorization_id,
            "egress": egress,
            "external_request_attempted": external_request_attempted,
            "external_response_received": external_response_received,
        }
        if destination is not None and destination.target_mode is TargetMode.REMOTE_AUTHORIZED:
            meta["transport"] = {"tls": "VERIFIED" if tls_verified else "NOT_ATTEMPTED"}
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
            payload={"operation": "reserve"},
        )

    def execute(self, operation: str, operation_context: Mapping[str, Any]) -> NativeResultEnvelope:
        op = operation.strip().lower()
        if op != "reserve":
            return self._failure("UNSUPPORTED_OPERATION", f"unsupported operation: {operation}")

        if not self._config.structurally_valid():
            return self._failure("ADAPTER_NOT_CONFIGURED", "adapter configuration invalid or disabled")

        if not self._config.credential_available():
            return self._failure("AUTH_CONFIG_MISSING", "required credential reference not available")

        path = self._config.allowed_paths[0] if self._config.allowed_paths else ""
        destination, verdict = self._policy.resolve_validated_destination(path)
        if verdict.decision is EgressDecision.DENY or destination is None:
            return self._failure(
                "EGRESS_DENIED",
                verdict.reason,
                egress_decision="DENY",
                egress_reason=verdict.reason,
            )

        body = self._map_request(operation_context)
        if body is None:
            return self._failure(
                "MAPPING_FAILURE",
                "structured input mapping failed",
                egress_decision="ALLOW",
                egress_reason=verdict.reason,
                destination=destination,
            )

        payload = json.dumps(body).encode("utf-8")
        if len(payload) > self._config.max_request_body_bytes:
            return self._failure(
                "REQUEST_TOO_LARGE",
                "request body exceeds size limit",
                egress_decision="ALLOW",
                egress_reason=verdict.reason,
                destination=destination,
            )

        started = time.monotonic()
        try:
            status, response_bytes, content_type = self._send_request(destination, payload)
        except TimeoutError:
            return self._failure(
                "NETWORK_TIMEOUT",
                "HTTP request timed out",
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

        try:
            parsed = json.loads(response_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._failure(
                "MALFORMED_EXTERNAL_RESPONSE",
                "invalid JSON response",
                attempted=True,
                received=True,
                egress_decision="ALLOW",
                egress_reason=verdict.reason,
                destination=destination,
            )

        native = self._map_response(parsed, timing_ms=timing_ms)
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

        tls_verified = destination.target_mode is TargetMode.REMOTE_AUTHORIZED
        self._set_metadata(
            external_request_attempted=True,
            external_response_received=True,
            egress_decision="ALLOW",
            egress_reason=verdict.reason,
            destination=destination,
            tls_verified=tls_verified,
        )
        return native

    def _auth_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        cred_var = self._config.credential_env_var
        if cred_var:
            token = os.environ.get(cred_var, "").strip()
            if token:
                headers["Authorization"] = f"Bearer {token}"
        return headers

    def _send_request(self, destination: ValidatedDestination, payload: bytes) -> tuple[int | None, bytes, str]:
        headers = self._auth_headers()
        timeout = self._config.timeout_seconds
        path = destination.request_path
        if destination.target_mode is TargetMode.REMOTE_AUTHORIZED:
            ssl_context = self._ssl_context_factory() if self._ssl_context_factory else None
            return bound_https_post_json(
                destination,
                path=path,
                headers=headers,
                body=payload,
                timeout=timeout,
                max_response_bytes=self._config.max_response_bytes,
                ssl_context=ssl_context,
            )
        return bound_http_post_json(
            destination,
            path=path,
            headers=headers,
            body=payload,
            timeout=timeout,
            max_response_bytes=self._config.max_response_bytes,
        )

    def _map_request(self, ctx: Mapping[str, Any]) -> dict[str, Any] | None:
        try:
            return {
                "date": str(ctx.get("date", "")),
                "time": str(ctx.get("time", "")),
                "party_size": int(ctx.get("party_size", 0)),
                "seating_type": str(ctx.get("seating_type", "")),
                "customer_reference": str(ctx.get("customer_reference") or "TEST-CUST-SYNTHETIC"),
                "idempotency_key": str(ctx.get("idempotency_key") or ctx.get("correlation_id") or ""),
            }
        except (TypeError, ValueError):
            return None

    def _map_response(self, data: Mapping[str, Any], *, timing_ms: int) -> NativeResultEnvelope | None:
        if not isinstance(data, dict):
            return None
        reservation_id = data.get("mock_reservation_id") or data.get("reservation_id")
        status = data.get("native_status") or data.get("status")
        if not reservation_id or not status:
            return None
        return NativeResultEnvelope(
            technical_status="TRANSPORT_OK",
            external_status=str(status),
            external_identifier=str(reservation_id),
            source=self.connector_id,
            timing_ms=timing_ms,
            payload={
                "operation": "reserve",
                "mock_native_result": dict(data),
                "classification": "EXTERNAL_BUSINESS_SYSTEM_TEST_DOUBLE",
                "semantic_authority": "NONE",
            },
        )
