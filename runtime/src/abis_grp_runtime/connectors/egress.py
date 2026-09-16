"""Simulator egress firewall — MOCK-ONLY, fail closed."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse


class EgressDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


ALLOWED_SIMULATOR_TARGET = "controlled-business-simulator"
ALLOWED_SIMULATOR_HOSTS = frozenset({"127.0.0.1", "localhost"})


@dataclass(frozen=True)
class EgressVerdict:
    decision: EgressDecision
    target: str
    reason: str


class SimulatorEgressFirewall:
    """
    Connector may access ONLY approved controlled business simulators.

    REAL EXTERNAL API · arbitrary URL · unapproved host · unknown target → DENY.
    """

    def evaluate_target(self, target: str) -> EgressVerdict:
        normalized = (target or "").strip().lower()
        if not normalized:
            return EgressVerdict(EgressDecision.DENY, target, "empty target — fail closed")
        if normalized == ALLOWED_SIMULATOR_TARGET:
            return EgressVerdict(EgressDecision.ALLOW, target, "approved simulator target")
        if normalized.startswith(("http://", "https://")):
            return EgressVerdict(EgressDecision.DENY, target, "arbitrary URL denied")
        return EgressVerdict(EgressDecision.DENY, target, "unknown target — fail closed")

    def evaluate_url(self, url: str) -> EgressVerdict:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https", ""):
            return EgressVerdict(EgressDecision.DENY, url, "unsupported scheme")
        if parsed.scheme in ("http", "https"):
            host = (parsed.hostname or "").lower()
            if host not in ALLOWED_SIMULATOR_HOSTS:
                return EgressVerdict(EgressDecision.DENY, url, "unapproved host denied")
            path = parsed.path or ""
            approved_paths = (
                "controlled-business-simulator",
                "controlled-reservation-simulator",
                "controlled-commerce-simulator",
                "/reservations",
            )
            if not any(marker in path for marker in approved_paths):
                return EgressVerdict(EgressDecision.DENY, url, "unapproved path denied")
        return self.evaluate_target(ALLOWED_SIMULATOR_TARGET)

    def require_simulator_target(self, target: str) -> None:
        verdict = self.evaluate_target(target)
        if verdict.decision is EgressDecision.DENY:
            raise PermissionError(verdict.reason)
