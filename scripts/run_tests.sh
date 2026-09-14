#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}/runtime/src:${ROOT}/reference-business/controlled-reservation-simulator/src:${ROOT}"
cd "${ROOT}"
python3 -m unittest discover -s tests -v
