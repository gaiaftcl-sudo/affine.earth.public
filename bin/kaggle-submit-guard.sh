#!/usr/bin/env bash
# Refuse Kaggle submit unless ALLOW_KAGGLE_SUBMIT=1.
# Usage:
#   source bin/kaggle-submit-guard.sh          # check only
#   bin/kaggle-submit-guard.sh CMD [args...]   # check then exec CMD
set -euo pipefail
_GUARD_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
_LOCK="$_GUARD_ROOT/configs/NO_KAGGLE_SUBMIT.lock"
if [[ -f "$_LOCK" && "${ALLOW_KAGGLE_SUBMIT:-}" != "1" ]]; then
  echo "BLOCKED: Kaggle submit refused (configs/NO_KAGGLE_SUBMIT.lock present)." >&2
  echo "Status polling (competitions submissions) is allowed; submit is not." >&2
  echo "To submit intentionally: ALLOW_KAGGLE_SUBMIT=1 <command>" >&2
  return 99 2>/dev/null || exit 99
fi
# When invoked as a program (not sourced), optionally exec the wrapped command.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]] && (($#)); then
  exec "$@"
fi
