"""Fail-closed non-production egress policy for authorized HTTP adapters."""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable
from urllib.parse import unquote, urlparse


class TargetMode(str, Enum):
    LOCALHOST_MOCK = "LOCALHOST_MOCK"
    REMOTE_AUTHORIZED = "REMOTE_AUTHORIZED"


class EnvironmentClassification(str, Enum):
    SANDBOX = "SANDBOX"
    MOCK = "MOCK"
    SIMULATOR = "SIMULATOR"
    SYNTHETIC_DEV = "SYNTHETIC_DEV"
    PRODUCTION = "PRODUCTION"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def parse(cls, value: str | None) -> EnvironmentClassification:
        if not value or not str(value).strip():
            return cls.UNKNOWN
        text = str(value).strip().upper()
        try:
            return cls(text)
        except ValueError:
            return cls.UNKNOWN

    def potentially_allowed(self) -> bool:
        return self in {
            EnvironmentClassification.SANDBOX,
            EnvironmentClassification.MOCK,
            EnvironmentClassification.SIMULATOR,
            EnvironmentClassification.SYNTHETIC_DEV,
        }


class EgressDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


@dataclass(frozen=True)
class EgressVerdict:
    decision: EgressDecision
    allowlist_id: str
    reason: str
    resolved_host: str | None = None


@dataclass(frozen=True)
class ValidatedDestination:
    """Policy-validated network destination — actual connect target must match."""

    target_mode: TargetMode
    authorized_hostname: str
    authorized_port: int
    resolved_ips: tuple[str, ...]
    selected_ip: str
    request_path: str
    scheme: str


_LOCALHOST_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})

ResolveFn = Callable[[str, int], tuple[str, ...]]


def _default_resolve(host: str, port: int) -> tuple[str, ...]:
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError(f"DNS resolution failed: {exc}") from exc
    seen: set[str] = set()
    ordered: list[str] = []
    for info in infos:
        sockaddr = info[4]
        if not sockaddr:
            continue
        ip_text = sockaddr[0]
        if ip_text in seen:
            continue
        seen.add(ip_text)
        ordered.append(ip_text)
    if not ordered:
        raise ValueError("DNS resolution returned no addresses")
    return tuple(ordered)


def _normalize_hostname(hostname: str) -> str:
    text = hostname.strip().rstrip(".")
    if not text:
        raise ValueError("missing hostname")
    if "*" in text:
        raise ValueError("wildcard hostnames not permitted")
    try:
        ascii_host = text.encode("idna").decode("ascii")
    except (UnicodeError, ValueError) as exc:
        raise ValueError("invalid hostname") from exc
    return ascii_host.lower()


def _hostname_is_ip_literal(hostname: str) -> bool:
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False


def _normalize_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        return ip.ipv4_mapped
    return ip


def _in_network(ip: ipaddress.IPv4Address | ipaddress.IPv6Address, network: str) -> bool:
    return ip in ipaddress.ip_network(network, strict=False)


def _ip_allowed_localhost_mock(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    ip = _normalize_ip(ip)
    return bool(ip.is_loopback)


def _ip_allowed_for_target_mode(
    mode: TargetMode,
    ip: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> bool:
    if mode is TargetMode.LOCALHOST_MOCK:
        return _ip_allowed_localhost_mock(ip)
    return _ip_allowed_remote_public(ip)


def _ip_allowed_remote_public(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    ip = _normalize_ip(ip)
    if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast:
        return False
    if ip.is_reserved or ip.is_unspecified:
        return False
    if ip == ipaddress.ip_address("169.254.169.254"):
        return False
    if isinstance(ip, ipaddress.IPv4Address):
        if _in_network(ip, "0.0.0.0/8"):
            return False
        if _in_network(ip, "100.64.0.0/10"):
            return False
        if _in_network(ip, "192.0.0.0/24"):
            return False
        if _in_network(ip, "192.0.2.0/24"):
            return False
        if _in_network(ip, "198.18.0.0/15"):
            return False
        if _in_network(ip, "198.51.100.0/24"):
            return False
        if _in_network(ip, "203.0.113.0/24"):
            return False
        if _in_network(ip, "240.0.0.0/4"):
            return False
        return ip.is_global
    if isinstance(ip, ipaddress.IPv6Address):
        if _in_network(ip, "fc00::/7") or _in_network(ip, "fe80::/10"):
            return False
        if _in_network(ip, "100::/64"):
            return False
        if _in_network(ip, "2001:db8::/32"):
            return False
        return ip.is_global
    return False


def _canonicalize_allowed_path(path: str) -> str | None:
    if not path or not path.startswith("/"):
        return None
    if "?" in path or "#" in path:
        return None
    segments: list[str] = []
    for segment in path.split("/"):
        if segment in ("",):
            continue
        decoded = unquote(segment)
        if decoded in (".", ".."):
            return None
        if "%" in segment and decoded != segment and unquote(unquote(segment)) != decoded:
            return None
        segments.append(decoded)
    return "/" + "/".join(segments) if segments else "/"


class NonProductionEgressPolicy:
    """
    Reference Runtime safety policy — not normative ABIS.

    No arbitrary URL proxy: target must match trusted configuration only.
    """

    def __init__(
        self,
        *,
        allowlist_id: str,
        target_mode: TargetMode,
        authorized_hostname: str,
        authorized_port: int,
        allowed_paths: tuple[str, ...],
        environment_classification: EnvironmentClassification,
        target_authorization_id: str,
        base_url: str | None = None,
        resolve_fn: ResolveFn | None = None,
    ) -> None:
        self._allowlist_id = allowlist_id.strip()
        self._target_mode = target_mode
        self._authorized_hostname = _normalize_hostname(authorized_hostname)
        self._authorized_port = int(authorized_port)
        self._allowed_paths = tuple(_canonicalize_allowed_path(p) or "" for p in allowed_paths)
        self._environment = environment_classification
        self._target_authorization_id = target_authorization_id.strip()
        self._base_url = (base_url or "").strip().rstrip("/") or None
        self._resolve = resolve_fn or _default_resolve
        self._validate_config_consistency()

    def _validate_config_consistency(self) -> None:
        if self._target_mode is TargetMode.REMOTE_AUTHORIZED:
            if _hostname_is_ip_literal(self._authorized_hostname):
                raise ValueError("IP literal hostname not permitted for remote authorized mode")
        if self._base_url:
            parsed = urlparse(self._base_url)
            if parsed.hostname:
                normalized = _normalize_hostname(parsed.hostname)
                if normalized != self._authorized_hostname:
                    raise ValueError("base_url hostname inconsistent with authorized_hostname")
            if parsed.port and parsed.port != self._authorized_port:
                raise ValueError("base_url port inconsistent with authorized_port")
            expected_scheme = "https" if self._target_mode is TargetMode.REMOTE_AUTHORIZED else "http"
            if parsed.scheme and parsed.scheme != expected_scheme:
                raise ValueError("base_url scheme inconsistent with target_mode")
            if self._target_mode is TargetMode.REMOTE_AUTHORIZED and parsed.scheme == "http":
                raise ValueError("HTTP not permitted for remote authorized mode")

    @property
    def allowlist_id(self) -> str:
        return self._allowlist_id

    @property
    def target_mode(self) -> TargetMode:
        return self._target_mode

    @property
    def target_authorization_id(self) -> str:
        return self._target_authorization_id

    def evaluate_environment(self) -> EgressVerdict:
        if not self._allowlist_id:
            return EgressVerdict(EgressDecision.DENY, "", "missing allowlist_id")
        if not self._target_authorization_id:
            return EgressVerdict(EgressDecision.DENY, self._allowlist_id, "missing target_authorization_id")
        if not self._environment.potentially_allowed():
            return EgressVerdict(
                EgressDecision.DENY,
                self._allowlist_id,
                f"environment classification {self._environment.value} denied",
            )
        if self._authorized_port <= 0 or self._authorized_port > 65535:
            return EgressVerdict(EgressDecision.DENY, self._allowlist_id, "invalid authorized port")
        return EgressVerdict(EgressDecision.ALLOW, self._allowlist_id, "environment permitted")

    def resolve_validated_destination(self, configured_path: str) -> tuple[ValidatedDestination | None, EgressVerdict]:
        env_verdict = self.evaluate_environment()
        if env_verdict.decision is EgressDecision.DENY:
            return None, env_verdict

        canonical = _canonicalize_allowed_path(configured_path)
        if canonical is None or canonical not in self._allowed_paths:
            return None, EgressVerdict(
                EgressDecision.DENY,
                self._allowlist_id,
                "path not in allowed_paths",
            )

        host = self._authorized_hostname
        if self._target_mode is TargetMode.LOCALHOST_MOCK:
            if host not in _LOCALHOST_HOSTS:
                return None, EgressVerdict(
                    EgressDecision.DENY,
                    self._allowlist_id,
                    "localhost mock requires loopback hostname",
                )
            scheme = "http"
        else:
            scheme = "https"
            if host in _LOCALHOST_HOSTS:
                return None, EgressVerdict(
                    EgressDecision.DENY,
                    self._allowlist_id,
                    "loopback hostname not permitted for remote authorized mode",
                )

        try:
            resolved = self._resolve(host, self._authorized_port)
        except ValueError as exc:
            return None, EgressVerdict(EgressDecision.DENY, self._allowlist_id, str(exc))

        normalized_ips: list[str] = []
        for ip_text in resolved:
            try:
                ip_obj = ipaddress.ip_address(ip_text)
            except ValueError:
                return None, EgressVerdict(EgressDecision.DENY, self._allowlist_id, "invalid resolved address")
            ip_obj = _normalize_ip(ip_obj)
            if not _ip_allowed_for_target_mode(self._target_mode, ip_obj):
                return None, EgressVerdict(
                    EgressDecision.DENY,
                    self._allowlist_id,
                    "prohibited resolved address in DNS answer",
                )
            normalized_ips.append(str(ip_obj))

        if not normalized_ips:
            return None, EgressVerdict(
                EgressDecision.DENY,
                self._allowlist_id,
                "no policy-permitted resolved addresses",
            )

        selected = sorted(set(normalized_ips))[0]
        destination = ValidatedDestination(
            target_mode=self._target_mode,
            authorized_hostname=host,
            authorized_port=self._authorized_port,
            resolved_ips=tuple(sorted(set(normalized_ips))),
            selected_ip=selected,
            request_path=canonical,
            scheme=scheme,
        )
        return destination, EgressVerdict(
            EgressDecision.ALLOW,
            self._allowlist_id,
            "egress permitted",
            resolved_host=host,
        )

    def resolve_request_url(self, path: str) -> tuple[str | None, EgressVerdict]:
        """Legacy helper — returns synthetic URL for logging only; connect uses ValidatedDestination."""
        destination, verdict = self.resolve_validated_destination(path)
        if destination is None:
            return None, verdict
        return (
            f"{destination.scheme}://{destination.authorized_hostname}:{destination.authorized_port}"
            f"{destination.request_path}",
            verdict,
        )
