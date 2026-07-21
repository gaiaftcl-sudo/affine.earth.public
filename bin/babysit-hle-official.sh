#!/usr/bin/env bash
# Long-running HLE official babysitter. Never prints tokens. No Kaggle.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="${PID_FILE:-/tmp/hle_full_pid.txt}"
DIR_FILE="${DIR_FILE:-/tmp/hle_full_dir.txt}"
PRED="$ROOT/harnesses/hle/hle_eval/hle_qwen3.6-35b-a3b.json"
JUDGED="$ROOT/harnesses/hle/hle_eval/judged_hle_qwen3.6-35b-a3b.json"
LOG="${BABYSIT_LOG:-$ROOT/reports/hle_official_20260721T143509Z/babysit.log}"
INTERVAL="${BABYSIT_INTERVAL_SECONDS:-300}"
mkdir -p "$(dirname "$LOG")"

ensure_finalize() {
  if pgrep -f 'watch-hle-official-finalize.sh' >/dev/null 2>&1; then
    return 0
  fi
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) restarting finalize watcher" | tee -a "$LOG"
  nohup env OPENAI_MODEL=qwen/qwen3.6-35b-a3b HLE_JUDGE_MODEL=qwen/qwen3.6-35b-a3b \
    "$ROOT/bin/watch-hle-official-finalize.sh" >>/tmp/hle_finalize_watch.log 2>&1 &
}

restart_harness() {
  local run_dir
  run_dir="$(cat "$DIR_FILE")"
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) RESTART harness from checkpoint" | tee -a "$LOG"
  # Load token from hub cache only — never echo
  if [[ -z "${HF_TOKEN:-}" && -f "$HOME/.cache/huggingface/token" ]]; then
    HF_TOKEN="$(cat "$HOME/.cache/huggingface/token")"
    export HF_TOKEN HUGGING_FACE_HUB_TOKEN="$HF_TOKEN"
  fi
  export OPENAI_BASE_URL="${OPENAI_BASE_URL:-http://127.0.0.1:8080/v1}"
  export OPENAI_API_KEY="${OPENAI_API_KEY:-uum8d-hle-verifier}"
  export OPENAI_MODEL="${OPENAI_MODEL:-qwen/qwen3.6-35b-a3b}"
  export AFFINE_HARNESS_MODEL="$OPENAI_MODEL"
  export HLE_JUDGE_MODEL="${HLE_JUDGE_MODEL:-$OPENAI_MODEL}"
  export HLE_OUTPUT_DIR="$run_dir"
  unset HLE_MAX_SAMPLES || true
  export HLE_RUN_JUDGE=1
  export HLE_NUM_WORKERS="${HLE_NUM_WORKERS:-4}"
  export HLE_MAX_COMPLETION_TOKENS="${HLE_MAX_COMPLETION_TOKENS:-768}"
  nohup env \
    HF_TOKEN="${HF_TOKEN:-}" HUGGING_FACE_HUB_TOKEN="${HUGGING_FACE_HUB_TOKEN:-${HF_TOKEN:-}}" \
    OPENAI_BASE_URL="$OPENAI_BASE_URL" OPENAI_API_KEY="$OPENAI_API_KEY" \
    OPENAI_MODEL="$OPENAI_MODEL" AFFINE_HARNESS_MODEL="$OPENAI_MODEL" \
    HLE_JUDGE_MODEL="$HLE_JUDGE_MODEL" \
    HLE_OUTPUT_DIR="$HLE_OUTPUT_DIR" HLE_RUN_JUDGE=1 \
    HLE_NUM_WORKERS="$HLE_NUM_WORKERS" HLE_MAX_COMPLETION_TOKENS="$HLE_MAX_COMPLETION_TOKENS" \
    "$ROOT/bin/run-open-agi-harnesses.sh" --harness hle \
    >>"$run_dir/harness.log" 2>&1 &
  echo $! >"$PID_FILE"
  ensure_finalize
}

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) babysit start" | tee -a "$LOG"
while true; do
  ensure_finalize
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  alive=n
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then alive=y; fi
  # Also detect orphaned prediction child
  if [[ "$alive" != "y" ]] && pgrep -f 'run_model_predictions.py' >/dev/null 2>&1; then
    alive=y
  fi
  n=0
  if [[ -f "$PRED" ]]; then
    n="$(python3 -c "import json; print(len(json.load(open(r'''$PRED'''))))")"
  fi
  judged=0
  if [[ -f "$JUDGED" ]]; then
    judged="$(python3 -c "import json; print(len(json.load(open(r'''$JUDGED'''))))")"
  fi
  receipt="$(cat "$DIR_FILE" 2>/dev/null)/official_hle_accuracy.receipt.json"
  acc="null"
  if [[ -f "$receipt" ]]; then
    acc="$(python3 -c "import json; print(json.load(open(r'''$receipt''')).get('official_hle_accuracy'))")"
  fi
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) preds=$n/2500 judged=$judged alive=$alive pid=${pid:-none} acc=$acc" | tee -a "$LOG"

  if [[ -f "$receipt" && "$acc" != "null" && "$acc" != "None" ]]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) COMPLETE official_hle_accuracy=$acc" | tee -a "$LOG"
    exit 0
  fi

  if [[ "$alive" != "y" ]]; then
    if [[ "$n" -ge 2500 && -f "$JUDGED" ]]; then
      echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) harness done; waiting finalize" | tee -a "$LOG"
      ensure_finalize
    elif [[ "$n" -ge 2500 ]]; then
      # Predictions done but judge missing — restart to run judge phase
      restart_harness
    else
      restart_harness
    fi
  fi
  sleep "$INTERVAL"
done
