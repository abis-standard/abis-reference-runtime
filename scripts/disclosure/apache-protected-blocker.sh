#!/usr/bin/env bash
# M229D-004 — Apache repository protected-code blocker (generic structural markers only)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FAIL=0

BLOCKED_PATH_FRAGMENTS=(
  "outcome_testbed"
)

BLOCKED_CODE_PATTERNS=(
  'outcome_equivalence_engine'
  'determine_business_outcome'
  'class OutcomeEquivalenceEngine'
  'class NormalizationEngine'
  'class CrossBusinessEvaluator'
  'def normalize_outcome'
  'def evaluate_equivalence'
  'class OutcomeResultPatternTestbed'
)

# Implementation scan roots only — tests/docs may reference forbidden terms negatively
IMPL_ROOTS=(
  "${ROOT}/runtime/src"
  "${ROOT}/reference-business"
  "${ROOT}/scripts"
)

while IFS= read -r -d '' file; do
  rel="${file#${ROOT}/}"
  for frag in "${BLOCKED_PATH_FRAGMENTS[@]}"; do
    if [[ "$rel" == *"$frag"* ]]; then
      FAIL=1
    fi
  done
done < <(find "${ROOT}" -type f ! -path '*/.git/*' ! -path '*/__pycache__/*' -print0)

for impl_root in "${IMPL_ROOTS[@]}"; do
  [[ -d "${impl_root}" ]] || continue
  while IFS= read -r -d '' file; do
    rel="${file#${ROOT}/}"
    case "$rel" in
      scripts/disclosure/apache-protected-blocker.sh)
        continue
        ;;
    esac
    for pattern in "${BLOCKED_CODE_PATTERNS[@]}"; do
      if grep -qF "$pattern" "$file" 2>/dev/null; then
        FAIL=1
      fi
    done
    # Block affirmative outcome_evaluation payloads in implementation code
    if grep -qE '"outcome_evaluation"\s*:\s*\{' "$file" 2>/dev/null; then
      FAIL=1
    fi
    if grep -qE 'outcome_evaluation\s*=\s*comparison' "$file" 2>/dev/null; then
      FAIL=1
    fi
  done < <(find "${impl_root}" -type f \( -name '*.py' -o -name '*.sh' \) ! -path '*/__pycache__/*' -print0)
done

if [[ "${FAIL}" -eq 1 ]]; then
  echo "M229D-004 BLOCK: Protected disclosure policy violation." >&2
  exit 1
fi

echo "M229D-004 PASS"
exit 0
