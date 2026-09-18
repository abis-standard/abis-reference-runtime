#!/usr/bin/env bash
# M229D-008 — Generic secrets scan (public-safe patterns only)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FAIL=0

PATTERNS=(
  '/Users/'
  'C:\\Users\\'
  'PRIVATE_MASTER'
  'INTERNAL_ONLY'
  'BEGIN RSA PRIVATE KEY'
  'BEGIN OPENSSH PRIVATE KEY'
  'BEGIN EC PRIVATE KEY'
  'AKIA[0-9A-Z]{16}'
  'ghp_[A-Za-z0-9]{20,}'
  'xox[baprs]-'
)

while IFS= read -r file; do
  case "$file" in
    */scripts/disclosure/check-secrets.sh|*/tests/test_m229d_disclosure_synthetic.py)
      continue
      ;;
  esac
  for pattern in "${PATTERNS[@]}"; do
    if [[ "$pattern" == AKIA* ]] || [[ "$pattern" == ghp_* ]] || [[ "$pattern" == xox* ]]; then
      if grep -qE "$pattern" "$file" 2>/dev/null; then
        FAIL=1
      fi
    elif grep -qF "$pattern" "$file" 2>/dev/null; then
      FAIL=1
    fi
  done
done < <(find "${ROOT}" -type f ! -path '*/.git/*' ! -path '*/__pycache__/*' \
  \( -name '*.md' -o -name '*.yml' -o -name '*.yaml' -o -name '*.txt' -o -name '*.py' -o -name '*.sh' -o -name '*.json' -o -name 'LICENSE' \) \
  | sort)

if [[ "${FAIL}" -eq 1 ]]; then
  echo "M229D-008 BLOCK: Disclosure policy violation detected." >&2
  exit 1
fi

echo "M229D-008 PASS"
exit 0
