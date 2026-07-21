#!/usr/bin/env bash
# Local macOS ARC UI audit runner. This command has no Kaggle capability.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ARC_AUDIT_PYTHON:-python3}"

if [[ ! -f "$ROOT/configs/NO_KAGGLE_SUBMIT.lock" ]]; then
  echo "ERROR: configs/NO_KAGGLE_SUBMIT.lock is required; refusing to run." >&2
  exit 2
fi

command -v "$PYTHON_BIN" >/dev/null || {
  echo "ERROR: Python not found; set ARC_AUDIT_PYTHON." >&2
  exit 127
}

exec "$PYTHON_BIN" "$ROOT/scripts/arc_ui_audit_orchestrator.py" "$@"
