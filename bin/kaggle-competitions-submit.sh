#!/usr/bin/env bash
# Safe wrapper: kaggle competitions submit ... (blocked unless ALLOW_KAGGLE_SUBMIT=1)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/bin/kaggle-submit-guard.sh"
exec kaggle competitions submit "$@"
