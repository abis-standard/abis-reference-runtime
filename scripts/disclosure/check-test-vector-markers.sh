#!/usr/bin/env bash
# M229D-009 — Public-safe protected test vector marker enforcement
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FAIL=0

MARKERS=(
  "protected_golden_vectors"
  "counsel_derived_test_cases"
  "patent_embodiment_fixtures"
  "private_simulator_scenario_internals"
  "SYNTHETIC_PROTECTED_TEST_VECTOR"
)

SCAN_ROOTS=(
  "${ROOT}/tests"
  "${ROOT}/examples"
  "${ROOT}/validation"
  "${ROOT}/runtime/src"
  "${ROOT}/reference-business"
)

for scan_root in "${SCAN_ROOTS[@]}"; do
  [[ -d "${scan_root}" ]] || continue
  while IFS= read -r -d '' file; do
    rel="${file#${ROOT}/}"
    case "$rel" in
      scripts/disclosure/check-test-vector-markers.sh|tests/test_m229d_disclosure_synthetic.py)
        continue
        ;;
    esac
    for marker in "${MARKERS[@]}"; do
      if grep -qF "$marker" "$file" 2>/dev/null; then
        FAIL=1
      fi
    done
  done < <(find "${scan_root}" -type f ! -path '*/__pycache__/*' -print0)
done

if [[ "${FAIL}" -eq 1 ]]; then
  echo "M229D-009 BLOCK: Disclosure policy violation." >&2
  exit 1
fi

echo "M229D-009 PASS"
exit 0
