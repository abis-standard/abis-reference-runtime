#!/usr/bin/env python3
"""Start ABIS Reference Runtime demo gateway — localhost bind, MOCK-ONLY."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SRC = ROOT / "runtime" / "src"
CRS_SRC = ROOT / "reference-business" / "controlled-reservation-simulator" / "src"
for path in (RUNTIME_SRC, CRS_SRC):
    sys.path.insert(0, str(path))

from crs.engine import ReservationEngine  # noqa: E402
from abis_grp_runtime.e2e.service import GrokE2EService  # noqa: E402
from abis_grp_runtime.gateway.config import GatewayConfig  # noqa: E402
from abis_grp_runtime.gateway.server import gateway_public_base_url, start_external_gateway  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="ABIS Reference Runtime demo gateway (MOCK-ONLY)")
    parser.add_argument("--host", default=os.environ.get("ABIS_DEMO_GATEWAY_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("ABIS_DEMO_GATEWAY_PORT", "9080")))
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Persistent directory for reference business state (state.json). Recommended for local use.",
    )
    parser.add_argument(
        "--evidence-log",
        default=os.environ.get("ABIS_DEMO_GATEWAY_EVIDENCE_LOG"),
        help="Optional JSONL evidence log path (no secrets logged)",
    )
    args = parser.parse_args()

    config = GatewayConfig.from_env()
    config = GatewayConfig(
        host=args.host,
        port=args.port,
        mode=config.mode,
        bearer_token=config.bearer_token,
        max_body_bytes=config.max_body_bytes,
        requests_per_minute=config.requests_per_minute,
        max_concurrent=config.max_concurrent,
        request_timeout_seconds=config.request_timeout_seconds,
        tls_cert_file=config.tls_cert_file,
        tls_key_file=config.tls_key_file,
        evidence_log_path=args.evidence_log or config.evidence_log_path,
    )
    config.validate_startup()

    if not args.data_dir:
        print("Warning: --data-dir not set; reservation state will not persist across restarts.")
        print("         Use: --data-dir ./data")
        data_dir = os.path.join(os.getcwd(), ".abis-reference-runtime-tmp")
        os.makedirs(data_dir, exist_ok=True)
    else:
        data_dir = args.data_dir
        os.makedirs(data_dir, exist_ok=True)

    engine = ReservationEngine(data_dir=data_dir)
    service = GrokE2EService(engine)
    httpd, port, _ = start_external_gateway(service, config, quiet=False)
    base = gateway_public_base_url(config, port)

    print(f"ABIS Reference Runtime gateway listening on {base}")
    print(f"GET  {base}/v1/reference-profile")
    print(f"POST {base}/v1/demo/restaurant/invoke")
    print("GET  /health")
    print(f"ABIS_GATEWAY_MODE={config.mode}")
    print("Authorization: Bearer <ABIS_DEMO_GATEWAY_TOKEN>")
    print("MOCK-ONLY · NON-PRODUCTION · CONTROLLED_SIMULATOR")
    print(f"Business state: {Path(data_dir).resolve() / 'state.json'}")
    print("")
    print("Shutdown: Ctrl+C")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
        httpd.server_close()


if __name__ == "__main__":
    main()
