#!/usr/bin/env bash
# Permanent miss → reinject → closure loop for ARC-AGI-2/3 and HLE.
# Never submits to Kaggle. Requires configs/NO_KAGGLE_SUBMIT.lock.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

usage() {
  cat <<'EOF'
Usage: bin/run-exam-reinjection-loop.sh [options]

Loads local fail receipts (ARC-2/3, HLE), opens a Franklin turn with the
UUM-8D baseline + miss evidence, asks for S1–S4 repair + C4 lock, records
grammar updates, re-runs local mastery for affected tasks, and logs turn
count toward 29-turn Aristotelian closure.

Options (passed through to scripts/exam_miss_reinjection_loop.py):
  --once                 Single cycle (default)
  --daemon               Continuous re-run (never idle)
  --interval-seconds N   Daemon sleep between cycles (default 30)
  --max-cycles N         Stop daemon after N cycles (0 = forever)
  --tracks arc2,arc3,hle
  --per-track-limit N
  --mastery none|affected|full
  --dry-run              No Franklin HTTP (still records placeholders)
  --timeout N
  --help

Environment:
  EXAM_REINJECT_BASE_URL / OPENAI_BASE_URL / HLE_LOCAL_BASE_URL
  EXAM_REINJECT_FALLBACK_BASE_URL   (default http://127.0.0.1:1234/v1 on primary stall)
  EXAM_REINJECT_MODEL / OPENAI_MODEL / HLE_LOCAL_MODEL
  EXAM_REINJECT_TIMEOUT (default 300) / EXAM_REINJECT_MAX_TOKENS (default 1024)
  EXAM_REINJECT_LIVE=1              (forbids --dry-run mixed writers)
  OPENAI_API_KEY / AFFINE_HARNESS_API_KEY

See reports/exam_reinjection/env.local.example

Does NOT call Kaggle. Blocked by configs/NO_KAGGLE_SUBMIT.lock.
EOF
}

if [[ ! -f "$ROOT/configs/NO_KAGGLE_SUBMIT.lock" ]]; then
  echo "ERROR: configs/NO_KAGGLE_SUBMIT.lock missing — refuse to run." >&2
  exit 2
fi

if [[ "${ALLOW_KAGGLE_SUBMIT:-}" == "1" ]]; then
  echo "WARN: ALLOW_KAGGLE_SUBMIT=1 is set, but this script never submits." >&2
fi

ARGS=()
if (($# == 0)); then
  ARGS=(--once)
else
  for arg in "$@"; do
    case "$arg" in
      --help|-h) usage; exit 0 ;;
    esac
  done
  ARGS=("$@")
  # Default to --once when neither daemon nor once was provided.
  has_mode=0
  for arg in "${ARGS[@]}"; do
    case "$arg" in
      --once|--daemon) has_mode=1 ;;
    esac
  done
  if [[ "$has_mode" -eq 0 ]]; then
    ARGS=(--once "${ARGS[@]}")
  fi
fi

PYTHON_BIN="${EXAM_REINJECT_PYTHON:-${ARC_LOCAL_PYTHON:-python3}}"
exec "$PYTHON_BIN" "$ROOT/scripts/exam_miss_reinjection_loop.py" --root "$ROOT" "${ARGS[@]}"
