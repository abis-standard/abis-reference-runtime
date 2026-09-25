#!/usr/bin/env python3
"""Localhost-only Mock Restaurant HTTP server — synthetic reservations, no real booking."""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from uuid import uuid4


class MockRestaurantHandler(BaseHTTPRequestHandler):
    server_version = "abis-mock-restaurant/1"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/health":
            self._send_json(200, {"ok": True, "service": "mock-restaurant"})
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/sandbox/v1/reservations":
            self._send_json(404, {"error": "not_found"})
            return
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid_json"})
            return
        reservation_id = f"MOCK-RSV-{uuid4().hex[:12].upper()}"
        response = {
            "mock_reservation_id": reservation_id,
            "native_status": "CONFIRMED",
            "reservation": {
                "date": body.get("date"),
                "time": body.get("time"),
                "party_size": body.get("party_size"),
                "seating_type": body.get("seating_type"),
                "customer_reference": body.get("customer_reference"),
                "synthetic": True,
            },
        }
        self._send_json(200, response)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    parser = argparse.ArgumentParser(description="ABIS Mock Restaurant HTTP server (localhost only)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9095)
    args = parser.parse_args()
    if args.host not in ("127.0.0.1", "localhost"):
        print("Mock server must bind to localhost only", file=sys.stderr)
        raise SystemExit(1)
    httpd = HTTPServer((args.host, args.port), MockRestaurantHandler)
    print(f"Mock Restaurant listening on http://{args.host}:{args.port}/sandbox/v1/reservations")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()


if __name__ == "__main__":
    main()
