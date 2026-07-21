#!/usr/bin/env bash
# Poll for HF auth usable by cais/hle. Never prints token values. No Keychain.
# When auth appears: prove load_dataset("cais/hle"), then kick official harness smoke.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
OUT="$ROOT/reports/hle_auth_wait"
mkdir -p "$OUT"
INTERVAL="${HLE_AUTH_POLL_SECONDS:-30}"
# 0 = poll forever (nohup steward wait)
MAX="${HLE_AUTH_POLL_MAX_SECONDS:-0}"
AUTO_KICK="${HLE_AUTH_AUTO_KICK:-1}"
SMOKE_SAMPLES="${HLE_AUTH_SMOKE_SAMPLES:-2}"

auth_present() {
  [[ -n "${HF_TOKEN:-}" || -n "${HUGGING_FACE_HUB_TOKEN:-}" ]] && return 0
  if [[ -f "$HOME/.cache/huggingface/token" ]] && [[ -s "$HOME/.cache/huggingface/token" ]]; then
    return 0
  fi
  return 1
}

prove_load() {
  local py="$ROOT/harnesses/hle/hle_eval/.venv/bin/python"
  [[ -x "$py" ]] || py="python3"
  # Export cache token into process env if only cache exists (never echo value).
  if [[ -z "${HF_TOKEN:-}" && -z "${HUGGING_FACE_HUB_TOKEN:-}" && -s "$HOME/.cache/huggingface/token" ]]; then
    export HF_TOKEN
    HF_TOKEN="$(tr -d '[:space:]' <"$HOME/.cache/huggingface/token")"
  fi
  "$py" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path
from datasets import load_dataset

out = Path("reports/hle_auth_wait")
out.mkdir(parents=True, exist_ok=True)
ds = load_dataset("cais/hle")
splits = {k: len(ds[k]) for k in ds.keys()} if hasattr(ds, "keys") else {"_": len(ds)}
receipt = {
    "kind": "hle_official_load_success",
    "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    "dataset": "cais/hle",
    "load_ok": True,
    "splits": splits,
    "n_rows_total": sum(splits.values()),
    "official_hle_accuracy": None,
    "official_claim_permitted": False,
    "notes": ["Load proved. Accuracy stays null until CAIS judge output exists."],
}
path = out / "dataset_load_success.json"
path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print("LOAD_OK splits=" + json.dumps(splits))
print("n_rows_total=" + str(receipt["n_rows_total"]))
print("receipt=" + str(path))
PY
}

kick_harness_smoke() {
  local stamp run_dir
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  run_dir="$ROOT/reports/hle_official_smoke_${stamp}"
  mkdir -p "$run_dir"
  echo "KICK_HARNESS_SMOKE dir=$run_dir samples=${SMOKE_SAMPLES} judge=0"
  # Judge refuses smoke subsets; predictions-only smoke proves authenticated path.
  (
    export HF_TOKEN="${HF_TOKEN:-${HUGGING_FACE_HUB_TOKEN:-}}"
    if [[ -z "${HF_TOKEN:-}" && -s "$HOME/.cache/huggingface/token" ]]; then
      HF_TOKEN="$(tr -d '[:space:]' <"$HOME/.cache/huggingface/token")"
      export HF_TOKEN
    fi
    export HLE_MAX_SAMPLES="${SMOKE_SAMPLES}"
    export HLE_RUN_JUDGE=0
    export HLE_OUTPUT_DIR="$run_dir"
    # Prefer existing loopback if steward already has OPENAI_* set; else defaults.
    export OPENAI_BASE_URL="${OPENAI_BASE_URL:-${AFFINE_HARNESS_ENDPOINT:-http://127.0.0.1:8080/v1}}"
    export OPENAI_API_KEY="${OPENAI_API_KEY:-${AFFINE_HARNESS_API_KEY:-uum8d-hle-verifier}}"
    export AFFINE_HARNESS_MODEL="${AFFINE_HARNESS_MODEL:-${OPENAI_MODEL:-}}"
    "$ROOT/bin/run-open-agi-harnesses.sh" --harness hle
  ) >"$run_dir/harness.log" 2>&1 || {
    echo "HARNESS_SMOKE_EXIT=$?" | tee -a "$run_dir/harness.log"
    return 1
  }
  echo "HARNESS_SMOKE_OK" | tee "$OUT/HARNESS_SMOKE_OK"
  echo "$run_dir" >"$OUT/latest_smoke_dir.txt"
}

if (( MAX > 0 )); then
  END=$(( $(date +%s) + MAX ))
  echo "Polling HF auth every ${INTERVAL}s for up to ${MAX}s (no token dump)..."
else
  END=0
  echo "Polling HF auth every ${INTERVAL}s forever until auth (no token dump)..."
fi

while true; do
  ENV_OK=0
  CACHE_OK=0
  [[ -n "${HF_TOKEN:-}" || -n "${HUGGING_FACE_HUB_TOKEN:-}" ]] && ENV_OK=1
  if [[ -f "$HOME/.cache/huggingface/token" ]] && [[ -s "$HOME/.cache/huggingface/token" ]]; then
    CACHE_OK=1
  fi
  TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  echo "{\"utc\":\"$TS\",\"env\":$ENV_OK,\"cache\":$CACHE_OK}" >>"$OUT/watch.jsonl"
  echo "POLL $TS env=$ENV_OK cache=$CACHE_OK"
  if auth_present; then
    echo "AUTH_APPEARED" | tee "$OUT/AUTH_APPEARED"
    if ! prove_load; then
      echo "LOAD_FAIL after auth" | tee "$OUT/LOAD_FAIL"
      exit 3
    fi
    echo "LOAD_OK" | tee "$OUT/LOAD_OK"
    if [[ "$AUTO_KICK" == "1" ]]; then
      kick_harness_smoke || echo "smoke kick non-zero; see reports/hle_official_smoke_*/harness.log"
    else
      echo "AUTO_KICK=0; steward should run HLE_RUN_JUDGE=1 ./bin/run-open-agi-harnesses.sh --harness hle"
    fi
    exit 0
  fi
  if (( MAX > 0 )) && (( $(date +%s) >= END )); then
    break
  fi
  sleep "$INTERVAL"
done

echo "AUTH_TIMEOUT" | tee "$OUT/AUTH_TIMEOUT"
echo "Steward: hf auth login   OR   export HF_TOKEN='hf_…'"
exit 2
