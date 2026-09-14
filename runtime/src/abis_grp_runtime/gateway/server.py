"""External demo gateway server startup."""

from __future__ import annotations

import ssl
import threading
from http.server import ThreadingHTTPServer
from typing import Any

from abis_grp_runtime.e2e.service import GrokE2EService
from abis_grp_runtime.gateway.config import GatewayConfig
from abis_grp_runtime.gateway.handler import ExternalDemoGatewayHandler
from abis_grp_runtime.gateway.rate_limit import RateLimitState


def make_handler_class(
    service: GrokE2EService,
    config: GatewayConfig,
    rate_limit: RateLimitState,
) -> type[ExternalDemoGatewayHandler]:
    return type(
        "ConfiguredExternalDemoGatewayHandler",
        (ExternalDemoGatewayHandler,),
        {"service": service, "config": config, "rate_limit": rate_limit},
    )


def start_external_gateway(
    service: GrokE2EService,
    config: GatewayConfig,
    *,
    quiet: bool = True,
) -> tuple[ThreadingHTTPServer, int, threading.Thread]:
    config.validate_startup()
    rate_limit = RateLimitState(
        requests_per_minute=config.requests_per_minute,
        max_concurrent=config.max_concurrent,
    )
    handler = make_handler_class(service, config, rate_limit)
    httpd = ThreadingHTTPServer((config.host, config.port), handler)
    httpd.timeout = config.request_timeout_seconds  # type: ignore[attr-defined]
    httpd.quiet = quiet  # type: ignore[attr-defined]

    if config.tls_cert_file and config.tls_key_file:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(config.tls_cert_file, config.tls_key_file)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

    bound_port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, bound_port, thread


def gateway_public_base_url(config: GatewayConfig, bound_port: int) -> str:
    scheme = "https" if config.tls_cert_file else "http"
    return f"{scheme}://{config.host}:{bound_port}"
