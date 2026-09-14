"""stdlib HTTP server for Controlled Reservation Simulator."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Type

from crs.api import handle_request
from crs.engine import ReservationEngine


def make_handler(engine: ReservationEngine) -> Type[BaseHTTPRequestHandler]:
    class CRSHandler(BaseHTTPRequestHandler):
        def _headers_dict(self):
            return {k: v for k, v in self.headers.items()}

        def _read_body(self) -> bytes:
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0:
                return b""
            return self.rfile.read(length)

        def _respond(self, code: int, payload: dict) -> None:
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("X-CRS-Classification", "EXTERNAL_BUSINESS_SYSTEM_TEST_DOUBLE")
            self.send_header("X-CRS-Semantic-Authority", "NONE")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):  # noqa: N802
            code, body = handle_request(engine, "GET", self.path, self._headers_dict(), b"")
            self._respond(code, body)

        def do_POST(self):  # noqa: N802
            code, body = handle_request(
                engine, "POST", self.path, self._headers_dict(), self._read_body()
            )
            self._respond(code, body)

        def do_PATCH(self):  # noqa: N802
            code, body = handle_request(
                engine, "PATCH", self.path, self._headers_dict(), self._read_body()
            )
            self._respond(code, body)

        def do_DELETE(self):  # noqa: N802
            code, body = handle_request(
                engine, "DELETE", self.path, self._headers_dict(), self._read_body()
            )
            self._respond(code, body)

        def log_message(self, fmt: str, *args) -> None:  # noqa: A003
            # Keep quiet in tests; still usable when run as __main__.
            if getattr(self.server, "crs_quiet", False):
                return
            super().log_message(fmt, *args)

    return CRSHandler


def serve(host: str = "127.0.0.1", port: int = 8765, data_dir: str = "./data") -> None:
    engine = ReservationEngine(data_dir=data_dir)
    handler = make_handler(engine)
    httpd = ThreadingHTTPServer((host, port), handler)
    httpd.crs_quiet = False  # type: ignore[attr-defined]
    print(
        f"CRS MOCK-ONLY listening on http://{host}:{port} data_dir={data_dir} "
        f"(REAL_BOOKING NONE, semantic_authority=NONE)"
    )
    httpd.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Controlled Reservation Simulator (MOCK-ONLY TEST DOUBLE)"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir", default="./data")
    args = parser.parse_args()
    serve(host=args.host, port=args.port, data_dir=args.data_dir)


if __name__ == "__main__":
    main()
