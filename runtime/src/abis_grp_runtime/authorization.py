"""Authorization boundary — fail-closed enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class AuthorizationState(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    DENIED = "DENIED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class AuthorizationDisposition:
    state: AuthorizationState
    reason: str

    @property
    def allowed(self) -> bool:
        return self.state is AuthorizationState.AUTHORIZED


@dataclass(frozen=True)
class AuthorizationInput:
    """Consumes upstream authority concepts without redefining them."""

    permission_token: str | None
    scope: Mapping[str, str] | None = None


def evaluate_authorization(auth_input: AuthorizationInput) -> AuthorizationDisposition:
    """Fail closed: unknown or missing authorization denies."""
    if auth_input.permission_token is None:
        return AuthorizationDisposition(
            state=AuthorizationState.UNKNOWN,
            reason="Missing permission token — fail closed",
        )
    token = auth_input.permission_token.strip()
    if not token:
        return AuthorizationDisposition(
            state=AuthorizationState.UNKNOWN,
            reason="Empty permission token — fail closed",
        )
    if token.upper() == "DENY":
        return AuthorizationDisposition(
            state=AuthorizationState.DENIED,
            reason="Explicit denial",
        )
    if token.upper() == "UNKNOWN":
        return AuthorizationDisposition(
            state=AuthorizationState.UNKNOWN,
            reason="Unknown authorization state — fail closed",
        )
    return AuthorizationDisposition(
        state=AuthorizationState.AUTHORIZED,
        reason="Permission token accepted",
    )
