#!/usr/bin/env bash
# Local-first HLE move-type drills. Never reads Keychain or writes a leaderboard score.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export HLE_LOCAL_BASE_URL="${HLE_LOCAL_BASE_URL:-${OPENAI_BASE_URL:-http://127.0.0.1:8080/v1}}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-${AFFINE_HARNESS_API_KEY:-uum8d-hle-verifier}}"

exec python3 scripts/run_local_hle_mastery.py "$@"
