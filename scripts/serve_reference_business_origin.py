#!/usr/bin/env python3
"""Serve a synthetic Reference Business Origin with a Runtime Pointer (stdlib only)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime" / "src"))

from abis_grp_runtime.discovery.pointer import (  # noqa: E402
    POINTER_WELL_KNOWN_PATH,
    build_reference_runtime_pointer,
)


class ReferenceBusinessOriginHandler(BaseHTTPRequestHandler):
    pointer_body: bytes
    server_version = "ABISReferenceBusinessOrigin/0.1"

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        if os.environ.get("ABIS_ORIGIN_QUIET") == "1":
            return
        super().log_message(format, *args)

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path == POINTER_WELL_KNOWN_PATH:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(self.pointer_body)))
            self.end_headers()
            self.wfile.write(self.pointer_body)
            return
        self.send_response(404)
        self.end_headers()


def main() -> int:
    parser = argparse.ArgumentParser(description="Reference Business Origin (synthetic)")
    parser.add_argument("--runtime-base-url", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()

    pointer = build_reference_runtime_pointer(args.runtime_base_url)
    pointer_body = json.dumps(pointer, sort_keys=True).encode("utf-8")

    handler = ReferenceBusinessOriginHandler
    handler.pointer_body = pointer_body
    httpd = ThreadingHTTPServer((args.host, args.port), handler)
    host, port = httpd.server_address
    origin = f"http://{host}:{port}"
    print(f"Reference Business Origin listening on {origin}")
    print(f"GET {origin}{POINTER_WELL_KNOWN_PATH}")
    print("SYNTHETIC · NON-PRODUCTION · POINTER ONLY")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nshutdown")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
