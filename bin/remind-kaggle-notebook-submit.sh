#!/usr/bin/env bash
# Print / optionally wait for Kaggle daily quota reset, then remind notebook submit.
# Does NOT submit. Does NOT unlock configs/NO_KAGGLE_SUBMIT.lock.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# From reports/kaggle_submit_20260721T173500Z/submit_batch.receipt.json
# 2026-07-21T17:39:04Z + 6.3h
RESET_EPOCH="${KAGGLE_QUOTA_RESET_EPOCH:-$(date -uj -f '%Y-%m-%dT%H:%M:%SZ' '2026-07-21T23:57:04Z' '+%s' 2>/dev/null || python3 - <<'PY'
from datetime import datetime, timezone
print(int(datetime(2026,7,21,23,57,4,tzinfo=timezone.utc).timestamp()))
PY
)}"

WAIT=0
while (($#)); do
  case "$1" in
    --wait) WAIT=1; shift ;;
    --reset-epoch) RESET_EPOCH="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

now=$(date -u '+%s')
remaining=$((RESET_EPOCH - now))
reset_iso=$(python3 - <<PY
from datetime import datetime, timezone
print(datetime.fromtimestamp($RESET_EPOCH, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
PY
)

echo "KAGGLE_NOTEBOOK_SUBMIT_REMINDER"
echo "quota_reset_utc=$reset_iso"
echo "remaining_seconds=$remaining"
echo "agi2_notebook=$ROOT/kaggle/airgap-notebooks/arc-agi-2/affine-agi2-airgap-submit.ipynb"
echo "agi3_notebook=$ROOT/kaggle/airgap-notebooks/arc-agi-3/affine-agi3-airgap-submit.ipynb"
echo "checklist=$ROOT/docs/KAGGLE_ARC_NOTEBOOK_SUBMIT.md"
echo "lock=$ROOT/configs/NO_KAGGLE_SUBMIT.lock (KEEP)"
echo "direct_cli=BLOCKED unless steward ALLOW_KAGGLE_SUBMIT=1 (still Notebooks-only)"
echo "standing_refs=AGI-2 54875115/0.00 AGI-3 54875048/0.12"
echo "action=After reset: upload notebook → Run All → Submit (do not competitions-submit raw files)"

if (( remaining > 0 && WAIT == 1 )); then
  echo "waiting ${remaining}s until quota reset…"
  sleep "$remaining"
  echo "QUOTA_WINDOW_OPEN utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) — steward: notebook Submit only"
elif (( remaining <= 0 )); then
  echo "QUOTA_WINDOW_OPEN (reset epoch already passed)"
fi
