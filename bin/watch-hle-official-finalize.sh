#!/usr/bin/env bash
# Wait for an in-flight official HLE harness PID; finalize receipt; reinject; wiki FoT; push.
# Never prints HF tokens. No Kaggle. Survives mid-write prediction JSON.
set +e
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="${1:-/tmp/hle_full_pid.txt}"
DIR_FILE="${2:-/tmp/hle_full_dir.txt}"
MODEL="${OPENAI_MODEL:-qwen/qwen3.6-35b-a3b}"
JUDGE="${HLE_JUDGE_MODEL:-$MODEL}"
BASE="$(basename "$MODEL")"
PRED="$ROOT/harnesses/hle/hle_eval/hle_${BASE}.json"
JUDGED="$ROOT/harnesses/hle/hle_eval/judged_hle_${BASE}.json"

read_pred_n() {
  python3 - <<PY
import json, time
from pathlib import Path
p = Path(r'''$PRED''')
for _ in range(12):
    try:
        print(len(json.loads(p.read_text())))
        raise SystemExit(0)
    except Exception:
        time.sleep(0.25)
print(-1)
PY
}

echo "watching pid_file=$PID_FILE run_dir_file=$DIR_FILE"
while true; do
  PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "${PID:-}" ]] && kill -0 "$PID" 2>/dev/null; then
    n="$(read_pred_n)"
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) preds=$n pid=$PID"
    sleep 60
    continue
  fi
  # Also treat live prediction child as still running even if wrapper pid flipped.
  if pgrep -f 'run_model_predictions.py' >/dev/null 2>&1; then
    n="$(read_pred_n)"
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) preds=$n wrapper_dead_but_predictor_alive"
    sleep 60
    continue
  fi
  break
done

RUN_DIR="$(cat "$DIR_FILE")"
echo "harness exited; finalizing run_dir=$RUN_DIR"
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

REINJECT_COUNT=0
if [[ -f "$RUN_DIR/misses.json" ]]; then
  REINJECT_COUNT="$(python3 -c "import json; print(len(json.load(open(r'''$RUN_DIR/misses.json'''))))")"
fi
echo "official_miss_count=$REINJECT_COUNT"
if [[ "$REINJECT_COUNT" -gt 0 ]]; then
  python3 "$ROOT/scripts/queue_hle_official_misses.py" --run-dir "$RUN_DIR" || true
  if [[ ! -f "$ROOT/reports/exam_reinjection/daemon.lock" ]]; then
    EXAM_REINJECT_TRACKS=hle EXAM_REINJECT_LIMIT=16 \
      "$ROOT/bin/run-exam-reinjection-loop.sh" --once \
      >"$RUN_DIR/reinject.log" 2>&1 || true
  else
    echo "exam reinjection daemon.lock held; misses queued only" | tee -a "$RUN_DIR/reinject.log"
  fi
fi

python3 "$ROOT/scripts/update_hle_wiki_fot.py" --run-dir "$RUN_DIR" || true

cd "$ROOT"
git add wiki/Humanitys-Last-Exam-Live.md wiki/Results-And-Scores.md wiki/Language-Games-HLE.md \
  "$RUN_DIR/official_hle_accuracy.receipt.json" 2>/dev/null || true
if ! git diff --cached --quiet 2>/dev/null; then
  git commit -m "$(cat <<'EOF'
feat(hle): seal official_hle_accuracy from judged cais/hle run

FoT Accuracy from upstream judge divisor n=2500. No token material.
EOF
)" || true
  GIT_SSH_COMMAND='ssh -i ~/.ssh/gaiaftcl_sudo_ed25519 -o IdentitiesOnly=yes' \
    git push origin HEAD || true
fi
echo "DONE rotate_reminder: rotate any chat-pasted HF token after this exam run"
echo "REINJECT_COUNT=$REINJECT_COUNT"
