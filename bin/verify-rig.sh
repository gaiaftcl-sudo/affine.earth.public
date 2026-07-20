#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

live=0
if [[ "${1:-}" == "--live" ]]; then
  live=1
elif [[ $# -ne 0 ]]; then
  echo "Usage: $0 [--live]" >&2
  exit 2
fi

python3 -m pytest tests/ -v

if [[ "$live" -eq 1 ]]; then
  : "${AFFINE_HEALTHCHECK_URL:?Set AFFINE_HEALTHCHECK_URL before --live verification.}"
  python3 scripts/verify_real_numbers_no_flub.py --live-url "$AFFINE_HEALTHCHECK_URL"
else
  python3 scripts/verify_real_numbers_no_flub.py
fi

echo "Verification passed."
