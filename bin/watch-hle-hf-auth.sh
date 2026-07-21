#!/usr/bin/env bash
# Poll for HF auth usable by cais/hle. Never prints token values. No Keychain.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/reports/hle_auth_wait"
mkdir -p "$OUT"
INTERVAL="${HLE_AUTH_POLL_SECONDS:-30}"
MAX="${HLE_AUTH_POLL_MAX_SECONDS:-600}"
END=$(( $(date +%s) + MAX ))
echo "Polling HF auth every ${INTERVAL}s for up to ${MAX}s (no token dump)..."
while (( $(date +%s) < END )); do
  ENV_OK=0
  CACHE_OK=0
  [[ -n "${HF_TOKEN:-}" || -n "${HUGGING_FACE_HUB_TOKEN:-}" ]] && ENV_OK=1
  if [[ -f "$HOME/.cache/huggingface/token" ]] && [[ -s "$HOME/.cache/huggingface/token" ]]; then
    CACHE_OK=1
  fi
  TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  echo "{\"utc\":\"$TS\",\"env\":$ENV_OK,\"cache\":$CACHE_OK}" >>"$OUT/watch.jsonl"
  echo "POLL $TS env=$ENV_OK cache=$CACHE_OK"
  if (( ENV_OK == 1 || CACHE_OK == 1 )); then
    echo "AUTH_APPEARED" | tee "$OUT/AUTH_APPEARED"
    echo "Next:"
    echo "  harnesses/hle/hle_eval/.venv/bin/python -c \"from datasets import load_dataset; ds=load_dataset('cais/hle'); print({k:len(ds[k]) for k in ds})\""
    echo "  HLE_RUN_JUDGE=1 ./bin/run-open-agi-harnesses.sh --harness hle"
    exit 0
  fi
  sleep "$INTERVAL"
done
echo "AUTH_TIMEOUT" | tee "$OUT/AUTH_TIMEOUT"
echo "Steward: hf auth login   OR   export HF_TOKEN='hf_…'"
exit 2
