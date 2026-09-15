"""Provider-neutral Reference Agent Client — PROFILE → PREFLIGHT → INVOKE."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Mapping
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from abis_grp_runtime.gateway.preflight import PREFLIGHT_READY
from abis_grp_runtime.gateway.reference_profile import PROFILE_KIND

ABSOLUTE_URL_PATTERN = re.compile(r"(?i)^(https?://|//|file://|ftp://)")


class ReferenceClientError(Exception):
    """Reference client fail-closed error — no invoke attempted."""


@dataclass(frozen=True)
class ReferenceClientConfig:
    base_url: str
    vertical: str
    operation: str
    execution_class: str
    gateway_token: str | None = None
    timeout: float = 10.0


@dataclass(frozen=True)
class ReferenceClientResult:
    profile_checked: bool = False
    preflight_state: str | None = None
    invoke_attempted: bool = False
    transport_status: str | None = None
    native_external_status: str | None = None
    outcome_disposition: str | None = None
    trace_reference: dict[str, Any] | None = None
    reservation_id: str | None = None
    error: str | None = None
    profile: dict[str, Any] | None = field(default=None, repr=False)
    preflight: dict[str, Any] | None = field(default=None, repr=False)
    invoke_response: dict[str, Any] | None = field(default=None, repr=False)


class ReferenceAgentClient:
    """Minimal agent-side client for Discover Runtime Surface → Preflight → Invoke."""

    def __init__(self, config: ReferenceClientConfig) -> None:
        self.config = config
        self._base = config.base_url.rstrip("/")

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self._base}{path}"

    @staticmethod
    def validate_profile(profile: Any) -> None:
        if not isinstance(profile, dict):
            raise ReferenceClientError("profile must be a JSON object")
        if profile.get("profile_kind") != PROFILE_KIND:
            raise ReferenceClientError("invalid profile_kind")
        if profile.get("profile_version") is None:
            raise ReferenceClientError("missing profile_version")
        interactions = profile.get("advertised_interactions")
        if not isinstance(interactions, list):
            raise ReferenceClientError("invalid advertised_interactions")

    @staticmethod
    def locate_interaction(profile: Mapping[str, Any], *, vertical: str, operation: str) -> dict[str, Any]:
        vertical_norm = vertical.strip().lower()
        operation_norm = operation.strip().lower()
        for item in profile.get("advertised_interactions") or []:
            if not isinstance(item, dict):
                continue
            if item.get("vertical") == vertical_norm and item.get("operation") == operation_norm:
                return dict(item)
        raise ReferenceClientError("requested interaction not present in profile")

    @staticmethod
    def validate_invoke_target(invocation: Mapping[str, Any]) -> tuple[str, str]:
        method = str(invocation.get("method") or "").strip().upper()
        path = str(invocation.get("path") or "").strip()
        if method != "POST":
            raise ReferenceClientError("unsupported invoke method")
        if not path.startswith("/"):
            raise ReferenceClientError("invoke path must be relative")
        if ABSOLUTE_URL_PATTERN.search(path):
            raise ReferenceClientError("absolute invoke URL rejected")
        parsed = urlparse(path)
        if parsed.scheme or parsed.netloc:
            raise ReferenceClientError("absolute invoke URL rejected")
        return method, path

    def fetch_profile(self) -> dict[str, Any]:
        request = Request(self._url("/v1/reference-profile"), method="GET")
        return self._read_json(request)

    def run_preflight(self) -> dict[str, Any]:
        path = f"/v1/demo/{self.config.vertical.strip().lower()}/preflight"
        payload = {
            "operation": self.config.operation.strip().lower(),
            "execution_class": self.config.execution_class.strip().upper(),
        }
        request = Request(
            self._url(path),
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return self._read_json(request)

    def invoke(self, invoke_path: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        token = (self.config.gateway_token or "").strip()
        if not token:
            raise ReferenceClientError("gateway token missing")

        request = Request(
            self._url(invoke_path),
            data=json.dumps(dict(payload)).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        return self._read_json(request)

    def execute(self, invoke_payload: Mapping[str, Any]) -> ReferenceClientResult:
        profile: dict[str, Any] | None = None
        preflight: dict[str, Any] | None = None
        profile_checked = False
        try:
            profile = self.fetch_profile()
            self.validate_profile(profile)
            profile_checked = True
            interaction = self.locate_interaction(
                profile,
                vertical=self.config.vertical,
                operation=self.config.operation,
            )

            invocation = interaction.get("invocation") or {}
            self.validate_invoke_target(invocation)

            preflight = self.run_preflight()
            preflight_state = str(preflight.get("preflight_state") or "")
            if preflight_state != PREFLIGHT_READY:
                return ReferenceClientResult(
                    profile_checked=profile_checked,
                    preflight_state=preflight_state or None,
                    profile=profile,
                    preflight=preflight,
                    error="preflight not ready",
                )

            preflight_invocation = preflight.get("invocation") or {}
            _, invoke_path = self.validate_invoke_target(
                {
                    "method": preflight_invocation.get("method") or invocation.get("method"),
                    "path": preflight_invocation.get("path") or invocation.get("path"),
                }
            )

            if not (self.config.gateway_token or "").strip():
                return ReferenceClientResult(
                    profile_checked=profile_checked,
                    preflight_state=PREFLIGHT_READY,
                    profile=profile,
                    preflight=preflight,
                    error="gateway token missing",
                )

            response = self.invoke(invoke_path, invoke_payload)
            native = response.get("native_result") or {}
            outcome = response.get("outcome_disposition") or {}
            return ReferenceClientResult(
                profile_checked=profile_checked,
                preflight_state=PREFLIGHT_READY,
                invoke_attempted=True,
                transport_status=str(response.get("transport_status") or "") or None,
                native_external_status=native.get("external_status"),
                outcome_disposition=outcome.get("disposition"),
                trace_reference=dict(response.get("trace_reference") or {}),
                reservation_id=response.get("reservation_id"),
                profile=profile,
                preflight=preflight,
                invoke_response=response,
            )
        except ReferenceClientError as exc:
            return ReferenceClientResult(
                profile_checked=profile_checked,
                preflight_state=(preflight or {}).get("preflight_state") if preflight else None,
                profile=profile,
                preflight=preflight,
                error=str(exc),
            )
        except HTTPError as exc:
            body = self._decode_error_body(exc)
            message = body.get("error", {}).get("message") if isinstance(body, dict) else str(exc)
            return ReferenceClientResult(
                profile_checked=profile_checked,
                preflight_state=(preflight or {}).get("preflight_state") if preflight else None,
                profile=profile,
                preflight=preflight,
                error=message or f"HTTP {exc.code}",
            )

    def _read_json(self, request: Request) -> dict[str, Any]:
        with urlopen(request, timeout=self.config.timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        if not isinstance(body, dict):
            raise ReferenceClientError("expected JSON object response")
        return body

    @staticmethod
    def _decode_error_body(exc: HTTPError) -> Any:
        try:
            return json.loads(exc.read().decode("utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}


def gateway_token_from_env(env: Mapping[str, str] | None = None) -> str | None:
    """Read gateway token from environment without logging it."""
    source = env if env is not None else __import__("os").environ
    token = source.get("ABIS_DEMO_GATEWAY_TOKEN") or source.get("GROK_E2E_SHARED_SECRET")
    return token.strip() if token else None
