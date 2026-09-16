"""Business Adapter validation errors — implementation-level only."""

from __future__ import annotations


class AdapterValidationError(ValueError):
    """Vertical/operation structured_input validation failure."""

    def __init__(self, message: str, *, missing: str | None = None, fields: list[str] | None = None) -> None:
        super().__init__(message)
        self.missing = missing
        self.fields = fields or []
