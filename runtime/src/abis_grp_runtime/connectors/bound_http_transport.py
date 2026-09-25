"""Bound HTTP transport for localhost mock — connect to selected IP without re-DNS."""

from __future__ import annotations

import socket
from typing import Mapping

from abis_grp_runtime.connectors.non_production_egress import ValidatedDestination


def http_post_json(
    destination: ValidatedDestination,
    *,
    path: str,
    headers: Mapping[str, str],
    body: bytes,
    timeout: float,
    max_response_bytes: int,
) -> tuple[int, bytes, str]:
    sock = socket.create_connection(
        (destination.selected_ip, destination.authorized_port),
        timeout=timeout,
    )
    try:
        sock.settimeout(timeout)
        host_header = destination.authorized_hostname
        request_lines = [
            f"POST {path} HTTP/1.1",
            f"Host: {host_header}",
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
        return _read_http_response(sock, max_response_bytes=max_response_bytes)
    finally:
        try:
            sock.close()
        except OSError:
            pass


def _read_http_response(sock: socket.socket, *, max_response_bytes: int) -> tuple[int, bytes, str]:
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
    body = buffer[header_end + 4 :]

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
