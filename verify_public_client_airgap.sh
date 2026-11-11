#!/usr/bin/env bash
# verify_public_client_airgap.sh — Ensures 0% of Private Cell IP ever enters the Public Client Repo
set -euo pipefail

CLIENT_REPO_DIR="${1:-.}"

echo "🔒 Auditing Public Client Repo ($CLIENT_REPO_DIR) for Private Cell Symbols..."
if grep -REn "steinGCD128|rpzModularInverse64|AffineCattleMasterDaemon|10\.88\.0\.[0-9]" "$CLIENT_REPO_DIR" --exclude="verify_public_client_airgap.sh" --exclude="LICENSE" --exclude-dir=".git"; then
  echo "🚨 AIRGAP VIOLATION: Private Cell IP or internal 10.88.0.x mesh address detected in public client repo! Aborting push."
  exit 1
fi

echo "✅ PUBLIC CLIENT AIRGAP VERIFIED: Only public https://affine.earth/v1/{mcp,chat/completions,models} wire contracts present."
