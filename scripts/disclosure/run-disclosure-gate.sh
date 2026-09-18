#!/usr/bin/env bash
# M-229D public disclosure gate — abis-reference-runtime (Apache 2.0)
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${DIR}/../.." && pwd)"

echo "=== ABIS Reference Runtime Disclosure Gate (M-229D) ==="

"${DIR}/check-secrets.sh"
"${DIR}/apache-protected-blocker.sh"
"${DIR}/check-test-vector-markers.sh"
python3 "${DIR}/enforce-release-allowlist.py"
"${DIR}/verify-private-approval.sh"

# M229D-011 — semantic firewall regression (fail-closed)
cd "${ROOT}"
./scripts/run_tests.sh

echo "PUBLIC DISCLOSURE GATE: PASS"
