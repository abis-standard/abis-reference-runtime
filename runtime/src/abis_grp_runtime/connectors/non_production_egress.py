"""Fail-closed non-production egress policy for authorized HTTP adapters."""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from enum import Enum
from typing import Iterable
from urllib.parse import urljoin, urlparse


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


_LOCALHOST_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def _iter_resolved_ips(host: str) -> Iterable[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError(f"DNS resolution failed: {exc}") from exc
    seen: set[str] = set()
    for info in infos:
        sockaddr = info[4]
        if not sockaddr:
            continue
        ip_text = sockaddr[0]
        if ip_text in seen:
            continue
        seen.add(ip_text)
        yield ipaddress.ip_address(ip_text)


def _ip_allowed_for_egress(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if ip.is_loopback:
        return True
    if ip.is_private or ip.is_link_local or ip.is_reserved or ip.is_multicast:
        return False
    if ip == ipaddress.ip_address("169.254.169.254"):
        return False
    return False


class NonProductionEgressPolicy:
    """
    Reference Runtime safety policy — not normative ABIS.

    No arbitrary URL proxy: target URL must match configured base_url + allowed_paths.
    """

    def __init__(
        self,
        *,
        allowlist_id: str,
        base_url: str,
        allowed_paths: tuple[str, ...],
        environment_classification: EnvironmentClassification,
    ) -> None:
        self._allowlist_id = allowlist_id.strip()
        self._base_url = base_url.strip().rstrip("/")
        self._allowed_paths = tuple(p if p.startswith("/") else f"/{p}" for p in allowed_paths)
        self._environment = environment_classification

    @property
    def allowlist_id(self) -> str:
        return self._allowlist_id

    def evaluate_environment(self) -> EgressVerdict:
        if not self._allowlist_id:
            return EgressVerdict(EgressDecision.DENY, "", "missing allowlist_id")
        if not self._environment.potentially_allowed():
            return EgressVerdict(
                EgressDecision.DENY,
                self._allowlist_id,
                f"environment classification {self._environment.value} denied",
            )
        return EgressVerdict(EgressDecision.ALLOW, self._allowlist_id, "environment permitted")

    def resolve_request_url(self, path: str) -> tuple[str | None, EgressVerdict]:
        env_verdict = self.evaluate_environment()
        if env_verdict.decision is EgressDecision.DENY:
            return None, env_verdict

        normalized_path = path if path.startswith("/") else f"/{path}"
        if normalized_path not in self._allowed_paths:
            return None, EgressVerdict(
                EgressDecision.DENY,
                self._allowlist_id,
                "path not in allowed_paths",
            )

        base_parsed = urlparse(self._base_url)
        if base_parsed.scheme not in ("http", "https"):
            return None, EgressVerdict(EgressDecision.DENY, self._allowlist_id, "invalid base_url scheme")

        host = (base_parsed.hostname or "").lower()
        if not host:
            return None, EgressVerdict(EgressDecision.DENY, self._allowlist_id, "missing base_url host")

        is_localhost = host in _LOCALHOST_HOSTS
        if not is_localhost and base_parsed.scheme != "https":
            return None, EgressVerdict(
                EgressDecision.DENY,
                self._allowlist_id,
                "HTTPS required for non-localhost targets",
            )
        if not is_localhost:
            return None, EgressVerdict(
                EgressDecision.DENY,
                self._allowlist_id,
                "only explicit localhost HTTP targets permitted in reference adapter",
            )

        try:
            for ip in _iter_resolved_ips(host):
                if not _ip_allowed_for_egress(ip):
                    return None, EgressVerdict(
                        EgressDecision.DENY,
                        self._allowlist_id,
                        f"resolved address {ip} not permitted",
                    )
        except ValueError as exc:
            return None, EgressVerdict(EgressDecision.DENY, self._allowlist_id, str(exc))

        full_url = urljoin(f"{base_parsed.scheme}://{base_parsed.netloc}", normalized_path)
        return full_url, EgressVerdict(
            EgressDecision.ALLOW,
            self._allowlist_id,
            "egress permitted",
            resolved_host=host,
        )
