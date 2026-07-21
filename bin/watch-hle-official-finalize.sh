#!/usr/bin/env bash
# Wait for an in-flight official HLE harness PID; finalize receipt; reinject; wiki FoT; push.
# Never prints HF tokens. No Kaggle.
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

# Reinject official misses via Franklin S4 exam loop (HLE track only; no Kaggle).
REINJECT_COUNT=0
if [[ -f "$RUN_DIR/misses.json" ]]; then
  REINJECT_COUNT="$(python3 -c "import json; print(len(json.load(open(r'''$RUN_DIR/misses.json'''))))")"
fi
echo "official_miss_count=$REINJECT_COUNT"
if [[ "$REINJECT_COUNT" -gt 0 ]]; then
  # Queue official misses for exam reinjection grammar; run one HLE-focused cycle
  # without touching ARC daemon lock if held.
  python3 "$ROOT/scripts/queue_hle_official_misses.py" --run-dir "$RUN_DIR" || true
  if [[ ! -f "$ROOT/reports/exam_reinjection/daemon.lock" ]]; then
    EXAM_REINJECT_TRACKS=hle EXAM_REINJECT_LIMIT=16 \
      "$ROOT/bin/run-exam-reinjection-loop.sh" --once \
      >"$RUN_DIR/reinject.log" 2>&1 || true
  else
    echo "exam reinjection daemon.lock held; misses queued only" | tee -a "$RUN_DIR/reinject.log"
  fi
fi

# Wiki FoT score (no tokens)
python3 "$ROOT/scripts/update_hle_wiki_fot.py" --run-dir "$RUN_DIR" || true

# Push GaiaKey (main + wiki text already in tree)
cd "$ROOT"
if ! git diff --quiet -- wiki/Humanitys-Last-Exam-Live.md wiki/Results-And-Scores.md wiki/Language-Games-HLE.md 2>/dev/null \
  || ! git diff --cached --quiet 2>/dev/null; then
  git add wiki/Humanitys-Last-Exam-Live.md wiki/Results-And-Scores.md wiki/Language-Games-HLE.md \
    "$RUN_DIR/official_hle_accuracy.receipt.json" 2>/dev/null || true
  if ! git diff --cached --quiet; then
    git commit -m "$(cat <<'EOF'
feat(hle): seal official_hle_accuracy from judged cais/hle run

FoT Accuracy from upstream judge divisor n=2500. No token material.
EOF
)" || true
    GIT_SSH_COMMAND='ssh -i ~/.ssh/gaiaftcl_sudo_ed25519 -o IdentitiesOnly=yes' \
      git push origin HEAD || true
  fi
fi
echo "DONE rotate_reminder: rotate any chat-pasted HF token after this exam run"
echo "REINJECT_COUNT=$REINJECT_COUNT"
