#!/usr/bin/env bash
# Robust HLE official long monitor. Never prints tokens.
set +e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PRED="$ROOT/harnesses/hle/hle_eval/hle_qwen3.6-35b-a3b.json"
R="$ROOT/reports/hle_official_20260721T143509Z/official_hle_accuracy.receipt.json"
LOG="$ROOT/reports/hle_official_20260721T143509Z/long_monitor.log"

read_n() {
  python3 - <<'PY'
import json, time
from pathlib import Path
p = Path("harnesses/hle/hle_eval/hle_qwen3.6-35b-a3b.json")
for _ in range(12):
    try:
        print(len(json.loads(p.read_text())))
        raise SystemExit(0)
    except Exception:
        time.sleep(0.25)
print(-1)
PY
}

N0="$(read_n)"
T0="$(date +%s)"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) long_monitor start preds=$N0" | tee -a "$LOG"
for i in $(seq 1 120); do
  sleep 600
  N="$(read_n)"
  EL=$(( $(date +%s) - T0 ))
  if [[ "$N" -ge 0 && "$EL" -gt 0 ]]; then
    RATE="$(python3 -c "print(round(($N - $N0) / $EL * 60, 2))")"
    REM=$((2500 - N))
    ETA="$(python3 -c "r=max(($N - $N0) / $EL, 1e-12); print(round($REM / r / 3600, 1))")"
  else
    RATE="?"
    ETA="?"
  fi
  H=n
  kill -0 "$(cat /tmp/hle_full_pid.txt 2>/dev/null)" 2>/dev/null && H=y
  F=n
  pgrep -f 'watch-hle-official-finalize.sh' >/dev/null 2>&1 && F=y
  B=n
  pgrep -f 'babysit-hle-official.sh' >/dev/null 2>&1 && B=y
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) CHECKPOINT t=$((i * 10))m preds=$N/2500 rate=$RATE/min eta_h=$ETA harness=$H finalize=$F babysit=$B" | tee -a "$LOG"
  if [[ -f "$R" ]]; then
    python3 -c "import json; r=json.load(open('$R')); print('DONE', r.get('official_hle_accuracy'), r.get('miss_count'))" | tee -a "$LOG"
    exit 0
  fi
  if [[ "$F" != "y" ]]; then
    nohup env OPENAI_MODEL=qwen/qwen3.6-35b-a3b HLE_JUDGE_MODEL=qwen/qwen3.6-35b-a3b \
      "$ROOT/bin/watch-hle-official-finalize.sh" >>/tmp/hle_finalize_watch.log 2>&1 &
  fi
  if [[ "$B" != "y" ]]; then
    nohup "$ROOT/bin/babysit-hle-official.sh" >>"$ROOT/reports/hle_official_20260721T143509Z/babysit.log" 2>&1 &
  fi
done
