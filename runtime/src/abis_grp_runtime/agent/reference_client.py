"""Provider-neutral Reference Agent Client — DISCOVERY → PROFILE → PREFLIGHT → INVOKE."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Mapping
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from abis_grp_runtime.discovery.resolver import DiscoveryError, resolve_runtime_base_url
from abis_grp_runtime.descriptor.constants import DESCRIPTOR_KIND
from abis_grp_runtime.gateway.preflight import PREFLIGHT_READY
from abis_grp_runtime.gateway.reference_profile import PROFILE_KIND

ABSOLUTE_URL_PATTERN = re.compile(r"(?i)^(https?://|//|file://|ftp://)")
INVOKE_PATH_PREFIX = "/v1/demo/"


class _NoRedirectHandler(HTTPRedirectHandler):
    """Fail closed on HTTP redirects — prevents open-redirect / SSRF pivots."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise HTTPError(req.full_url, code, msg, headers, fp)


class ReferenceClientError(Exception):
    """Reference client fail-closed error — no invoke attempted."""


@dataclass(frozen=True)
class ReferenceClientConfig:
    vertical: str
    operation: str
    execution_class: str
    base_url: str | None = None
    business_origin: str | None = None
    gateway_token: str | None = None
    timeout: float = 10.0

    def __post_init__(self) -> None:
        has_base = bool((self.base_url or "").strip())
        has_origin = bool((self.business_origin or "").strip())
        if has_base and has_origin:
            raise ReferenceClientError("base_url and business_origin are mutually exclusive")
        if not has_base and not has_origin:
            raise ReferenceClientError("base_url or business_origin is required")


@dataclass(frozen=True)
class ReferenceClientResult:
    business_origin: str | None = None
    pointer_checked: bool = False
    runtime_base_url: str | None = None
    profile_checked: bool = False
    descriptor_checked: bool = False
    preflight_state: str | None = None
    invoke_attempted: bool = False
    transport_status: str | None = None
    native_external_status: str | None = None
    outcome_disposition: str | None = None
    trace_reference: dict[str, Any] | None = None
    native_external_identifier: str | None = None
    reservation_id: str | None = None
    correlation_id: str | None = None
    profile_version: int | None = None
    runtime_version: str | None = None
    execution_surface_revision: str | None = None
    error: str | None = None
    pointer: dict[str, Any] | None = field(default=None, repr=False)
    profile: dict[str, Any] | None = field(default=None, repr=False)
    preflight: dict[str, Any] | None = field(default=None, repr=False)
    invoke_response: dict[str, Any] | None = field(default=None, repr=False)
    descriptor: dict[str, Any] | None = field(default=None, repr=False)


class ReferenceAgentClient:
    """Agent-side client for Business Origin or Runtime Base URL → Preflight → Invoke."""

    def __init__(self, config: ReferenceClientConfig) -> None:
        self.config = config
        self._base = (config.base_url or "").rstrip("/")

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
        if ".." in path or "\\" in path or "\x00" in path:
            raise ReferenceClientError("invoke path traversal rejected")
        if not path.startswith(INVOKE_PATH_PREFIX):
            raise ReferenceClientError("invoke path outside gateway demo surface")
        if ABSOLUTE_URL_PATTERN.search(path):
            raise ReferenceClientError("absolute invoke URL rejected")
        parsed = urlparse(path)
        if parsed.scheme or parsed.netloc:
            raise ReferenceClientError("absolute invoke URL rejected")
        return method, path

    def discover_runtime(self) -> tuple[dict[str, Any], str]:
        origin = (self.config.business_origin or "").strip()
        if not origin:
            raise ReferenceClientError("business_origin missing")
        try:
            pointer, base_url = resolve_runtime_base_url(origin, timeout=self.config.timeout)
        except DiscoveryError as exc:
            raise ReferenceClientError(str(exc)) from exc
        self._base = base_url.rstrip("/")
        return pointer, base_url

    def fetch_profile(self) -> dict[str, Any]:
        request = Request(self._url("/v1/reference-profile"), method="GET")
        return self._read_json(request)

    @staticmethod
    def validate_descriptor(descriptor: Any) -> None:
        if not isinstance(descriptor, dict):
            raise ReferenceClientError("descriptor must be a JSON object")
        if descriptor.get("descriptor_kind") != DESCRIPTOR_KIND:
            raise ReferenceClientError("invalid descriptor_kind")
        if descriptor.get("descriptor_version") is None:
            raise ReferenceClientError("missing descriptor_version")
        structured = descriptor.get("structured_input")
        if not isinstance(structured, dict):
            raise ReferenceClientError("invalid structured_input section")

    def fetch_descriptor(self, descriptor_path: str) -> dict[str, Any]:
        path = descriptor_path.strip()
        if not path.startswith("/"):
            path = f"/{path}"
        request = Request(self._url(path), method="GET")
        return self._read_json(request)

    def run_preflight(self, *, correlation_id: str | None = None) -> dict[str, Any]:
        path = f"/v1/demo/{self.config.vertical.strip().lower()}/preflight"
        payload: dict[str, str] = {
            "operation": self.config.operation.strip().lower(),
            "execution_class": self.config.execution_class.strip().upper(),
        }
        if correlation_id:
            payload["correlation_id"] = correlation_id
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
        business_origin = (self.config.business_origin or "").strip() or None
        pointer: dict[str, Any] | None = None
        pointer_checked = False
        runtime_base_url = (self.config.base_url or "").strip() or None
        profile: dict[str, Any] | None = None
        descriptor: dict[str, Any] | None = None
        preflight: dict[str, Any] | None = None
        profile_checked = False
        descriptor_checked = False
        correlation_id = str(invoke_payload.get("correlation_id") or "").strip() or None

        try:
            if business_origin:
                pointer, runtime_base_url = self.discover_runtime()
                pointer_checked = True

            if not self._base:
                raise ReferenceClientError("runtime base URL unresolved")

            profile = self.fetch_profile()
            self.validate_profile(profile)
            profile_checked = True
            profile_version = profile.get("profile_version")
            runtime_version = (profile.get("runtime") or {}).get("version")
            execution_surface_revision = profile.get("execution_surface_revision")

            interaction = self.locate_interaction(
                profile,
                vertical=self.config.vertical,
                operation=self.config.operation,
            )

            descriptor_path = str(interaction.get("descriptor_path") or "").strip()
            if not descriptor_path:
                raise ReferenceClientError("descriptor_path missing from profile interaction")
            descriptor = self.fetch_descriptor(descriptor_path)
            self.validate_descriptor(descriptor)
            descriptor_checked = True

            invocation = interaction.get("invocation") or descriptor.get("invocation") or {}
            self.validate_invoke_target(invocation)

            preflight = self.run_preflight(correlation_id=correlation_id)
            preflight_state = str(preflight.get("preflight_state") or "")
            preflight_evidence = preflight.get("evidence") or {}
            if isinstance(preflight_evidence, dict):
                correlation_id = str(preflight_evidence.get("correlation_id") or correlation_id or "") or correlation_id
                execution_surface_revision = (
                    preflight_evidence.get("execution_surface_revision") or execution_surface_revision
                )
                runtime_version = preflight_evidence.get("runtime_version") or runtime_version
                profile_version = preflight_evidence.get("profile_version") or profile_version

            if preflight_state != PREFLIGHT_READY:
                return ReferenceClientResult(
                    business_origin=business_origin,
                    pointer_checked=pointer_checked,
                    runtime_base_url=runtime_base_url,
                    profile_checked=profile_checked,
                    descriptor_checked=descriptor_checked,
                    preflight_state=preflight_state or None,
                    correlation_id=correlation_id,
                    profile_version=profile_version if isinstance(profile_version, int) else None,
                    runtime_version=str(runtime_version) if runtime_version else None,
                    execution_surface_revision=(
                        str(execution_surface_revision) if execution_surface_revision else None
                    ),
                    pointer=pointer,
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
                    business_origin=business_origin,
                    pointer_checked=pointer_checked,
                    runtime_base_url=runtime_base_url,
                    profile_checked=profile_checked,
                    descriptor_checked=descriptor_checked,
                    preflight_state=PREFLIGHT_READY,
                    correlation_id=correlation_id,
                    profile_version=profile_version if isinstance(profile_version, int) else None,
                    runtime_version=str(runtime_version) if runtime_version else None,
                    execution_surface_revision=(
                        str(execution_surface_revision) if execution_surface_revision else None
                    ),
                    pointer=pointer,
                    profile=profile,
                    descriptor=descriptor,
                    preflight=preflight,
                    error="gateway token missing",
                )

            response = self.invoke(invoke_path, invoke_payload)
            if not isinstance(response, dict):
                raise ReferenceClientError("invoke response must be a JSON object")
            native = response.get("native_result") or {}
            if native and not isinstance(native, dict):
                raise ReferenceClientError("malformed native_result in invoke response")
            outcome = response.get("outcome_disposition") or {}
            if outcome and not isinstance(outcome, dict):
                raise ReferenceClientError("malformed outcome_disposition in invoke response")
            trace = response.get("trace_reference")
            if trace is not None and not isinstance(trace, dict):
                raise ReferenceClientError("malformed trace_reference in invoke response")
            trace_dict = dict(trace or {})
            if correlation_id and not trace_dict.get("correlation_id"):
                trace_dict["correlation_id"] = correlation_id
            native_external_identifier = native.get("external_identifier") or response.get(
                "native_external_identifier"
            )
            return ReferenceClientResult(
                business_origin=business_origin,
                pointer_checked=pointer_checked,
                runtime_base_url=runtime_base_url,
                profile_checked=profile_checked,
                descriptor_checked=descriptor_checked,
                preflight_state=PREFLIGHT_READY,
                invoke_attempted=True,
                transport_status=str(response.get("transport_status") or "") or None,
                native_external_status=native.get("external_status"),
                outcome_disposition=outcome.get("disposition"),
                trace_reference=trace_dict,
                native_external_identifier=str(native_external_identifier) if native_external_identifier else None,
                reservation_id=response.get("reservation_id") or native_external_identifier,
                correlation_id=correlation_id or trace_dict.get("correlation_id"),
                profile_version=profile_version if isinstance(profile_version, int) else None,
                runtime_version=str(runtime_version) if runtime_version else None,
                execution_surface_revision=str(execution_surface_revision) if execution_surface_revision else None,
                pointer=pointer,
                profile=profile,
                descriptor=descriptor,
                preflight=preflight,
                invoke_response=response,
            )
        except ReferenceClientError as exc:
            return ReferenceClientResult(
                business_origin=business_origin,
                pointer_checked=pointer_checked,
                runtime_base_url=runtime_base_url,
                profile_checked=profile_checked,
                descriptor_checked=descriptor_checked,
                preflight_state=(preflight or {}).get("preflight_state") if preflight else None,
                correlation_id=correlation_id,
                pointer=pointer,
                profile=profile,
                descriptor=descriptor,
                preflight=preflight,
                error=str(exc),
            )
        except HTTPError as exc:
            body = self._decode_error_body(exc)
            message = body.get("error", {}).get("message") if isinstance(body, dict) else str(exc)
            return ReferenceClientResult(
                business_origin=business_origin,
                pointer_checked=pointer_checked,
                runtime_base_url=runtime_base_url,
                profile_checked=profile_checked,
                descriptor_checked=descriptor_checked,
                preflight_state=(preflight or {}).get("preflight_state") if preflight else None,
                correlation_id=correlation_id,
                pointer=pointer,
                profile=profile,
                descriptor=descriptor,
                preflight=preflight,
                error=message or f"HTTP {exc.code}",
            )

    def _read_json(self, request: Request) -> dict[str, Any]:
        opener = build_opener(_NoRedirectHandler())
        with opener.open(request, timeout=self.config.timeout) as response:
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
