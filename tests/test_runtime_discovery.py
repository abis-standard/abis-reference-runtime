"""Business-origin Runtime discovery and agent flow tests."""

from __future__ import annotations

import json
import re
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.agent.reference_client import (  # noqa: E402
    ReferenceAgentClient,
    ReferenceClientConfig,
    ReferenceClientError,
)
from abis_grp_runtime.discovery.pointer import (  # noqa: E402
    POINTER_WELL_KNOWN_PATH,
    build_reference_runtime_pointer,
)
from abis_grp_runtime.discovery.resolver import DiscoveryError, resolve_runtime_base_url  # noqa: E402
from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.gateway.execution_surface import EXECUTION_SURFACE_REVISION  # noqa: E402
from abis_grp_runtime.gateway.preflight import PREFLIGHT_READY  # noqa: E402
from abis_grp_runtime.gateway.server import start_external_gateway  # noqa: E402
from tests._service import make_test_service  # noqa: E402

TEST_TOKEN = "test-gateway-token-discovery-do-not-commit"
FORBIDDEN_TERMS = (
    "ABIS Certified",
    "ABIS Conformant",
    "ABIS Compatible",
    "Capability Manifest",
    "/.well-known/abis",
)


def _invoke_payload(*, correlation_id: str = "discovery-flow-001") -> dict:
    return {
        "agent_id": "reference-agent-discovery",
        "agent_type": "reference-agent",
        "operation": "reserve",
        "execution_class": "CONTROLLED_SIMULATOR",
        "authorization_token": "ALLOW",
        "correlation_id": correlation_id,
        "input": {
            "date": "2026-09-16",
            "time": "19:00",
            "party_size": 2,
            "seating_type": "COUNTER",
            "customer_reference": "TEST-CUST-DISCOVERY",
            "idempotency_key": f"idem-{correlation_id}",
            "test_scenario": "NORMAL_SUCCESS",
        },
    }


class _PointerOriginHandler(BaseHTTPRequestHandler):
    pointer_json: bytes
    redirect: bool = False

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if self.redirect and path == POINTER_WELL_KNOWN_PATH:
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.1:1/evil")
            self.end_headers()
            return
        if path == POINTER_WELL_KNOWN_PATH:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(self.pointer_json)))
            self.end_headers()
            self.wfile.write(self.pointer_json)
            return
        self.send_response(404)
        self.end_headers()


class DiscoveryServerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.service = make_test_service(self.tmp.name)
        self.gateway_config = GatewayConfig(
            host="127.0.0.1",
            port=0,
            bearer_token=TEST_TOKEN,
            max_body_bytes=65536,
            requests_per_minute=120,
            max_concurrent=8,
        )
        self.httpd, self.gateway_port, _ = start_external_gateway(self.service, self.gateway_config)
        self.runtime_base = f"http://127.0.0.1:{self.gateway_port}"
        self.origin_httpd: ThreadingHTTPServer | None = None
        self.origin_port: int | None = None

    def tearDown(self) -> None:
        if self.origin_httpd is not None:
            self.origin_httpd.shutdown()
            self.origin_httpd.server_close()
        self.httpd.shutdown()
        self.httpd.server_close()
        self.tmp.cleanup()

    def _start_origin(self, *, runtime_base_url: str, redirect: bool = False) -> str:
        pointer = build_reference_runtime_pointer(runtime_base_url)
        handler = _PointerOriginHandler
        handler.pointer_json = json.dumps(pointer).encode("utf-8")
        handler.redirect = redirect
        self.origin_httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=self.origin_httpd.serve_forever, daemon=True)
        thread.start()
        self.origin_port = self.origin_httpd.server_address[1]
        return f"http://127.0.0.1:{self.origin_port}"

    def test_business_origin_to_runtime_url(self) -> None:
        origin = self._start_origin(runtime_base_url=self.runtime_base)
        pointer, base_url = resolve_runtime_base_url(origin)
        self.assertEqual(base_url, self.runtime_base)
        self.assertEqual(pointer["pointer_kind"], "abis-reference-runtime-pointer")

    def test_redirect_rejected(self) -> None:
        origin = self._start_origin(runtime_base_url=self.runtime_base, redirect=True)
        with self.assertRaises(DiscoveryError):
            resolve_runtime_base_url(origin)

    def test_invalid_scheme_rejected(self) -> None:
        with self.assertRaises(DiscoveryError):
            resolve_runtime_base_url("ftp://example.test")

    def test_malformed_origin_rejected(self) -> None:
        with self.assertRaises(DiscoveryError):
            resolve_runtime_base_url("not-a-url")

    def test_credentials_not_forwarded_to_origin(self) -> None:
        origin = self._start_origin(runtime_base_url=self.runtime_base)
        url = f"{origin}{POINTER_WELL_KNOWN_PATH}"
        req = Request(url, method="GET")
        with urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read().decode())
        self.assertEqual(body["runtime"]["base_url"], self.runtime_base)
        self.assertNotIn("Authorization", req.header_items())

    def test_unsafe_runtime_url_in_pointer_rejected(self) -> None:
        bad_pointer = {
            "pointer_kind": "abis-reference-runtime-pointer",
            "pointer_version": 1,
            "authority": {"semantic": "NONE", "normative": "NONE"},
            "runtime": {"base_url": "http://user:pass@127.0.0.1:9080"},
        }
        handler = _PointerOriginHandler
        handler.pointer_json = json.dumps(bad_pointer).encode("utf-8")
        handler.redirect = False
        self.origin_httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=self.origin_httpd.serve_forever, daemon=True)
        thread.start()
        origin = f"http://127.0.0.1:{self.origin_httpd.server_address[1]}"
        with self.assertRaises(DiscoveryError):
            resolve_runtime_base_url(origin)

    def test_business_origin_full_agent_flow(self) -> None:
        origin = self._start_origin(runtime_base_url=self.runtime_base)
        client = ReferenceAgentClient(
            ReferenceClientConfig(
                business_origin=origin,
                vertical="restaurant",
                operation="reserve",
                execution_class="CONTROLLED_SIMULATOR",
                gateway_token=TEST_TOKEN,
            )
        )
        result = client.execute(_invoke_payload())
        self.assertTrue(result.pointer_checked)
        self.assertTrue(result.profile_checked)
        self.assertEqual(result.preflight_state, PREFLIGHT_READY)
        self.assertTrue(result.invoke_attempted)
        self.assertEqual(result.outcome_disposition, "NOT_EVALUATED")
        self.assertEqual(result.runtime_base_url, self.runtime_base)
        self.assertEqual(result.execution_surface_revision, EXECUTION_SURFACE_REVISION)
        self.assertEqual(result.correlation_id, "discovery-flow-001")
        self.assertIsNotNone(result.trace_reference)

    def test_base_url_flow_still_works(self) -> None:
        client = ReferenceAgentClient(
            ReferenceClientConfig(
                base_url=self.runtime_base,
                vertical="restaurant",
                operation="reserve",
                execution_class="CONTROLLED_SIMULATOR",
                gateway_token=TEST_TOKEN,
            )
        )
        result = client.execute(_invoke_payload(correlation_id="base-url-flow-001"))
        self.assertFalse(result.pointer_checked)
        self.assertTrue(result.profile_checked)
        self.assertTrue(result.invoke_attempted)

    def test_mutually_exclusive_base_url_and_origin(self) -> None:
        with self.assertRaises(ReferenceClientError):
            ReferenceClientConfig(
                base_url=self.runtime_base,
                business_origin="http://127.0.0.1:1",
                vertical="restaurant",
                operation="reserve",
                execution_class="CONTROLLED_SIMULATOR",
            )

    def test_preflight_evidence_metadata(self) -> None:
        origin = self._start_origin(runtime_base_url=self.runtime_base)
        client = ReferenceAgentClient(
            ReferenceClientConfig(
                business_origin=origin,
                vertical="restaurant",
                operation="reserve",
                execution_class="CONTROLLED_SIMULATOR",
                gateway_token=TEST_TOKEN,
            )
        )
        client.discover_runtime()
        preflight = client.run_preflight(correlation_id="evidence-001")
        evidence = preflight.get("evidence") or {}
        self.assertEqual(evidence.get("correlation_id"), "evidence-001")
        self.assertEqual(evidence.get("execution_surface_revision"), EXECUTION_SURFACE_REVISION)
        self.assertIsNotNone(evidence.get("runtime_version"))
        self.assertIsNotNone(evidence.get("profile_version"))

    def test_real_external_still_denied(self) -> None:
        client = ReferenceAgentClient(
            ReferenceClientConfig(
                base_url=self.runtime_base,
                vertical="restaurant",
                operation="reserve",
                execution_class="REAL_EXTERNAL",
                gateway_token=TEST_TOKEN,
            )
        )
        result = client.execute(_invoke_payload(correlation_id="real-external-denied"))
        self.assertFalse(result.invoke_attempted)

    def test_pointer_semantic_firewall(self) -> None:
        pointer = build_reference_runtime_pointer(self.runtime_base)
        serialized = json.dumps(pointer)
        for term in FORBIDDEN_TERMS:
            self.assertNotIn(term, serialized)


class TestDiscoveryMalformedPointer(unittest.TestCase):
    def test_wrong_pointer_kind_over_http(self) -> None:
        class BadHandler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args) -> None:  # noqa: A003
                return

            def do_GET(self) -> None:
                body = json.dumps({"pointer_kind": "wrong"}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        httpd = ThreadingHTTPServer(("127.0.0.1", 0), BadHandler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        origin = f"http://127.0.0.1:{httpd.server_address[1]}"
        try:
            with self.assertRaises(DiscoveryError):
                resolve_runtime_base_url(origin)
        finally:
            httpd.shutdown()
            httpd.server_close()


if __name__ == "__main__":
    unittest.main()
