"""External demo gateway HTTP handler."""

from __future__ import annotations

import json
import re
import socket
from http.server import BaseHTTPRequestHandler
from typing import Any
from urllib.parse import urlparse

from abis_grp_runtime.e2e.service import GrokE2EService
from abis_grp_runtime.gateway.auth import extract_bearer_token, verify_bearer
from abis_grp_runtime.gateway.config import GatewayConfig
from abis_grp_runtime.gateway.errors import GatewayError, GatewayErrorCode
from abis_grp_runtime.gateway.evidence_log import append_evidence
from abis_grp_runtime.gateway.rate_limit import RateLimitState
from abis_grp_runtime.gateway.preflight import evaluate_preflight, parse_preflight_payload
from abis_grp_runtime.gateway.reference_profile import (
    DESCRIPTOR_PATH_PREFIX,
    REFERENCE_PROFILE_PATH,
    build_health_response,
    build_reference_runtime_profile,
)
from abis_grp_runtime.gateway.validation import validate_payload

INVOKE_PATH = re.compile(r"^/v1/demo/(?P<vertical>[a-z_]+)/invoke/?$")
PREFLIGHT_PATH = re.compile(r"^/v1/demo/(?P<vertical>[a-z_]+)/preflight/?$")
DESCRIPTOR_PATH = re.compile(
    r"^/v1/reference-profile/interactions/(?P<vertical>[a-z_]+)/(?P<operation>[a-z_]+)/?$"
)


class ExternalDemoGatewayHandler(BaseHTTPRequestHandler):
    service: GrokE2EService
    config: GatewayConfig
    rate_limit: RateLimitState

    server_version = "ABISDemoGateway/0.4"

    def log_message(self, format: str, *args: Any) -> None:
        if getattr(self.server, "quiet", False):  # type: ignore[attr-defined]
            return
        super().log_message(format, *args)

    @property
    def _client_key(self) -> str:
        return self.client_address[0] if self.client_address else "unknown"

    def _send_json(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _reject(self, error: GatewayError, *, correlation_id: str | None = None) -> None:
        append_evidence(
            self.config.evidence_log_path,
            {
                "correlation_id": correlation_id,
                "http_status": error.http_status,
                "transport_status": "REJECTED",
                "gateway_error_code": error.code.value,
            },
        )
        self._send_json(error.http_status, error.to_response(correlation_id=correlation_id))

    def _authenticate(self) -> bool:
        token = extract_bearer_token(self.headers.get("Authorization"))
        if not verify_bearer(token, self.config.bearer_token or ""):
            self._reject(
                GatewayError(
                    GatewayErrorCode.AUTHENTICATION_DENIED,
                    "authentication denied",
                    http_status=401,
                )
            )
            return False
        return True

    def do_GET(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/health":
            self._send_json(200, build_health_response(self.config))
            return
        if path == REFERENCE_PROFILE_PATH:
            self._send_json(200, build_reference_runtime_profile(self.config))
            return
        descriptor_match = DESCRIPTOR_PATH.match(path)
        if descriptor_match:
            vertical = descriptor_match.group("vertical")
            operation = descriptor_match.group("operation")
            try:
                body = self.service.registry.get_descriptor(vertical, operation)
            except KeyError:
                self._reject(GatewayError(GatewayErrorCode.REQUEST_INVALID, "not found", http_status=404))
                return
            self._send_json(200, body)
            return
        self._reject(GatewayError(GatewayErrorCode.REQUEST_INVALID, "not found", http_status=404))

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if PREFLIGHT_PATH.match(path):
            allowed, reason = self.rate_limit.allow(self._client_key)
            if not allowed:
                self._reject(
                    GatewayError(
                        GatewayErrorCode.RATE_LIMITED,
                        "rate limit exceeded",
                        http_status=429,
                        detail={"reason": reason},
                    )
                )
                return
            try:
                self._handle_preflight_post()
            finally:
                self.rate_limit.release(self._client_key)
            return

        if not self._authenticate():
            return

        allowed, reason = self.rate_limit.allow(self._client_key)
        if not allowed:
            self._reject(
                GatewayError(
                    GatewayErrorCode.RATE_LIMITED,
                    "rate limit exceeded",
                    http_status=429,
                    detail={"reason": reason},
                )
            )
            return

        try:
            self._handle_invoke_post()
        finally:
            self.rate_limit.release(self._client_key)

    def _read_json_body(self) -> tuple[dict[str, Any] | list[Any] | None, GatewayError | None]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None, GatewayError(
                GatewayErrorCode.REQUEST_INVALID,
                "invalid Content-Length",
                http_status=400,
            )

        if length > self.config.max_body_bytes:
            return None, GatewayError(
                GatewayErrorCode.REQUEST_INVALID,
                "request body too large",
                http_status=413,
                detail={"max_bytes": self.config.max_body_bytes},
            )

        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return None, GatewayError(
                GatewayErrorCode.REQUEST_INVALID,
                "invalid JSON",
                http_status=400,
            )
        return payload, None

    def _handle_preflight_post(self) -> None:
        path = urlparse(self.path).path
        match = PREFLIGHT_PATH.match(path)
        if not match:
            self._reject(GatewayError(GatewayErrorCode.REQUEST_INVALID, "unsupported route", http_status=404))
            return

        vertical = match.group("vertical")
        payload, error = self._read_json_body()
        if error:
            self._reject(error)
            return

        parsed, invalid = parse_preflight_payload(payload, vertical=vertical)
        if invalid is not None:
            self._send_json(200, invalid)
            return

        assert parsed is not None
        body = evaluate_preflight(
            self.config,
            vertical=vertical,
            operation=parsed["operation"],
            execution_class=parsed["execution_class"],
            correlation_id=parsed.get("correlation_id"),
        )
        self._send_json(200, body)

    def _handle_invoke_post(self) -> None:
        path = urlparse(self.path).path
        match = INVOKE_PATH.match(path)
        if not match:
            self._reject(GatewayError(GatewayErrorCode.REQUEST_INVALID, "unsupported route", http_status=404))
            return

        vertical = match.group("vertical")
        payload, error = self._read_json_body()
        if error:
            self._reject(error, correlation_id=None)
            return

        correlation_id = None
        if isinstance(payload, dict):
            correlation_id = str(payload.get("correlation_id") or "") or None

        if not isinstance(payload, dict):
            self._reject(GatewayError(GatewayErrorCode.REQUEST_INVALID, "JSON object required", http_status=400))
            return

        normalized, error = validate_payload(payload, vertical=vertical)
        if error:
            self._reject(error, correlation_id=correlation_id)
            return

        assert normalized is not None
        try:
            result = self.service.invoke_from_dict(normalized)
        except TimeoutError:
            self._reject(
                GatewayError(GatewayErrorCode.TIMEOUT, "request timed out", http_status=504),
                correlation_id=correlation_id,
            )
            return
        except Exception:
            self._reject(
                GatewayError(GatewayErrorCode.RUNTIME_ERROR, "runtime error", http_status=500),
                correlation_id=correlation_id,
            )
            return

        body = result.to_dict()
        auth = body.get("authorization_disposition") or {}
        execution = body.get("execution_disposition") or {}
        native = body.get("native_result") or {}
        outcome = body.get("outcome_disposition") or {}
        append_evidence(
            self.config.evidence_log_path,
            {
                "correlation_id": body.get("correlation_id"),
                "agent_type": (body.get("agent_identity") or {}).get("agent_type"),
                "vertical": vertical,
                "operation": normalized.get("operation"),
                "authorization_disposition": auth.get("state"),
                "execution_disposition": execution.get("execution_class"),
                "native_status": native.get("external_status"),
                "outcome_disposition": outcome.get("disposition"),
                "http_status": 200 if body.get("transport_status") == "ACCEPTED" else 422,
                "transport_status": body.get("transport_status"),
            },
        )
        status = 200 if body.get("transport_status") == "ACCEPTED" else 422
        self._send_json(status, body)
