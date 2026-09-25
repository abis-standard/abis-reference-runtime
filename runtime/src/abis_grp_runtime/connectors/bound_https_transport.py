"""Bound HTTPS transport — connect to policy-selected IP with verified TLS identity."""

from __future__ import annotations

import socket
import ssl
from typing import Mapping

from abis_grp_runtime.connectors.non_production_egress import ValidatedDestination


def default_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


class InsecureTlsContextError(OSError):
    """TLS context does not meet required verification invariants."""


def require_secure_tls_context(ctx: ssl.SSLContext) -> None:
    """Fail closed before connect when injected context disables verification."""
    if not ctx.check_hostname:
        raise InsecureTlsContextError("tls context rejected")
    if ctx.verify_mode != ssl.CERT_REQUIRED:
        raise InsecureTlsContextError("tls context rejected")


def connect_tls(
    destination: ValidatedDestination,
    *,
    timeout: float,
    ssl_context: ssl.SSLContext | None = None,
) -> ssl.SSLSocket:
    """TCP connect to selected_ip only; TLS with SNI + hostname verification."""
    ctx = ssl_context or default_ssl_context()
    require_secure_tls_context(ctx)
    raw = socket.create_connection(
        (destination.selected_ip, destination.authorized_port),
        timeout=timeout,
    )
    try:
        tls_sock = ctx.wrap_socket(
            raw,
            server_hostname=destination.authorized_hostname,
        )
    except Exception:
        raw.close()
        raise
    return tls_sock


def https_post_json(
    destination: ValidatedDestination,
    *,
    path: str,
    headers: Mapping[str, str],
    body: bytes,
    timeout: float,
    max_response_bytes: int,
    ssl_context: ssl.SSLContext | None = None,
) -> tuple[int, bytes, str]:
    """Minimal HTTPS POST without redirect following or hostname re-resolution."""
    sock = connect_tls(destination, timeout=timeout, ssl_context=ssl_context)
    try:
        sock.settimeout(timeout)
        request_lines = [
            f"POST {path} HTTP/1.1",
            f"Host: {destination.authorized_hostname}",
        ]
        for key, value in headers.items():
            if key.lower() == "host":
                continue
            request_lines.append(f"{key}: {value}")
        request_lines.append(f"Content-Length: {len(body)}")
        request_lines.append("")
        request_lines.append("")
        request_bytes = "\r\n".join(request_lines).encode("ascii") + body
        sock.sendall(request_bytes)

        response = _read_http_response(sock, max_response_bytes=max_response_bytes)
        return response
    finally:
        try:
            sock.close()
        except OSError:
            pass


def _read_http_response(sock: ssl.SSLSocket, *, max_response_bytes: int) -> tuple[int, bytes, str]:
    buffer = b""
    while b"\r\n\r\n" not in buffer and len(buffer) < max_response_bytes + 8192:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buffer += chunk

    header_end = buffer.find(b"\r\n\r\n")
    if header_end < 0:
        raise OSError("incomplete HTTP response")

    header_text = buffer[:header_end].decode("iso-8859-1", errors="replace")
    body_start = header_end + 4
    body = buffer[body_start:]

    status_line = header_text.split("\r\n", 1)[0]
    parts = status_line.split()
    if len(parts) < 2:
        raise OSError("malformed HTTP status line")
    status = int(parts[1])

    headers: dict[str, str] = {}
    for line in header_text.split("\r\n")[1:]:
        if ":" not in line:
            continue
        name, value = line.split(":", 1)
        headers[name.strip().lower()] = value.strip()

    if 300 <= status < 400:
        raise OSError("redirect not permitted")

    content_type = headers.get("content-type", "")
    transfer_encoding = headers.get("transfer-encoding", "").lower()
    if transfer_encoding == "chunked":
        body = _read_chunked_body(sock, initial=body, max_total=max_response_bytes + 1)
    else:
        content_length = headers.get("content-length")
        if content_length is not None:
            try:
                expected = int(content_length)
            except ValueError:
                raise OSError("invalid Content-Length") from None
            while len(body) < expected and len(body) <= max_response_bytes:
                chunk = sock.recv(min(4096, expected - len(body)))
                if not chunk:
                    break
                body += chunk
        else:
            while len(body) <= max_response_bytes:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                body += chunk

    if len(body) > max_response_bytes:
        raise OSError("response exceeds size limit")
    return status, body, content_type


def _read_chunked_body(sock: ssl.SSLSocket, *, initial: bytes, max_total: int) -> bytes:
    body = initial
    while True:
        line = b""
        while not line.endswith(b"\r\n"):
            chunk = sock.recv(1)
            if not chunk:
                break
            line += chunk
            if len(line) > 64:
                raise OSError("invalid chunked encoding")
        line = line.strip()
        if not line:
            continue
        size_part = line.split(b";", 1)[0]
        try:
            chunk_size = int(size_part, 16)
        except ValueError:
            raise OSError("invalid chunk size") from None
        if chunk_size == 0:
            break
        remaining = chunk_size
        while remaining > 0:
            if len(body) > max_total:
                raise OSError("response exceeds size limit")
            chunk = sock.recv(remaining)
            if not chunk:
                raise OSError("truncated chunked body")
            body += chunk
            remaining -= len(chunk)
        sock.recv(2)  # trailing CRLF after chunk data
    return body
