"""Client mTLS SSL context construction — verification invariants enforced."""

from __future__ import annotations

import ssl
from typing import Callable, Optional

from abis_grp_runtime.connectors.bound_https_transport import require_secure_tls_context

PassphraseProvider = Callable[[], Optional[str]]


class MtlsConfigurationError(ValueError):
    """Invalid or incomplete mTLS material."""


def build_client_mtls_context(
    *,
    certificate_path: str,
    private_key_path: str,
    passphrase_provider: PassphraseProvider | None = None,
    base_context: ssl.SSLContext | None = None,
) -> ssl.SSLContext:
    """Load client certificate chain with optional encrypted private key passphrase."""
    if not certificate_path or not private_key_path:
        raise MtlsConfigurationError("certificate and private key paths required")
    ctx = base_context or ssl.create_default_context()
    require_secure_tls_context(ctx)
    password: str | None = None
    if passphrase_provider is not None:
        raw = passphrase_provider()
        if raw is None or not str(raw):
            raise MtlsConfigurationError("private key passphrase unavailable")
        password = str(raw)
    try:
        ctx.load_cert_chain(certfile=certificate_path, keyfile=private_key_path, password=password)
    except OSError as exc:
        raise MtlsConfigurationError("client certificate chain load failed") from exc
    require_secure_tls_context(ctx)
    return ctx
