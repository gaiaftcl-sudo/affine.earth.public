#!/usr/bin/env bash
# Wait for an in-flight official HLE harness PID; finalize receipt; never print tokens.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="${1:-/tmp/hle_full_pid.txt}"
DIR_FILE="${2:-/tmp/hle_full_dir.txt}"
PID="$(cat "$PID_FILE")"
RUN_DIR="$(cat "$DIR_FILE")"
MODEL="${OPENAI_MODEL:-qwen/qwen3.6-35b-a3b}"
JUDGE="${HLE_JUDGE_MODEL:-$MODEL}"
BASE="$(basename "$MODEL")"
PRED="$ROOT/harnesses/hle/hle_eval/hle_${BASE}.json"
JUDGED="$ROOT/harnesses/hle/hle_eval/judged_hle_${BASE}.json"
echo "watching pid=$PID run_dir=$RUN_DIR"
while kill -0 "$PID" 2>/dev/null; do
  if [[ -f "$PRED" ]]; then
    n="$(python3 -c "import json; print(len(json.load(open(r'''$PRED'''))))")"
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) preds=$n"
  fi
  sleep 60
done
echo "harness exited; finalizing"
mkdir -p "$RUN_DIR"
[[ -f "$PRED" ]] && cp "$PRED" "$RUN_DIR/"
[[ -f "$JUDGED" ]] && cp "$JUDGED" "$RUN_DIR/"
if [[ ! -f "$JUDGED" ]]; then
  echo "FATAL: judged file missing after harness exit" >&2
  exit 2
fi
python3 "$ROOT/scripts/finalize_hle_official_receipt.py" \
  --run-dir "$RUN_DIR" \
  --judged "$JUDGED" \
  --predictions "$PRED" \
  --model "$MODEL" \
  --judge-model "$JUDGE"
