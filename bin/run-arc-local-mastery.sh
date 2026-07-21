#!/usr/bin/env bash
# Runs only local ARC validation. This command has no submission capability.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR=""
PYTHON_BIN="${ARC_LOCAL_PYTHON:-python3.12}"
PARQUET_PYTHON="${ARC_LOCAL_PARQUET_PYTHON:-python3}"

usage() {
  cat <<'EOF'
Usage: bin/run-arc-local-mastery.sh [--report-dir DIR]

Hard gates (must pass before mastery report is GREEN):
  1) fixtures/kaggle_arc_format/submission.json
       → scripts/validate_arc_prize_submission.py
  2) fixtures/kaggle_arc_format/submission.parquet
       → scripts/validate_arc_agi3_submission.py
  3) Offline language-game traces + official-data checks
       → scripts/arc_local_mastery.py
         (also re-runs top-score validators on local test submission.json
          and probe parquet)

Does NOT call Kaggle. Does NOT upload notebooks. Cannot submit.
Blocked by configs/NO_KAGGLE_SUBMIT.lock for any submit path.
EOF
}

while (($#)); do
  case "$1" in
    --report-dir) REPORT_DIR="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ ! -f "$ROOT/configs/NO_KAGGLE_SUBMIT.lock" ]]; then
  echo "ERROR: configs/NO_KAGGLE_SUBMIT.lock missing — refuse to run." >&2
  exit 2
fi

if [[ "${ALLOW_KAGGLE_SUBMIT:-}" == "1" ]]; then
  echo "WARN: ALLOW_KAGGLE_SUBMIT=1 is set, but this script never submits." >&2
fi

command -v "$PYTHON_BIN" >/dev/null || {
  echo "ARC local mastery requires Python 3.12; set ARC_LOCAL_PYTHON." >&2
  exit 127
}
command -v "$PARQUET_PYTHON" >/dev/null || {
  echo "Parquet validator python missing; set ARC_LOCAL_PARQUET_PYTHON." >&2
  exit 127
}

echo "== Hard gate: AGI-2 fixture (top-score JSON) =="
"$PYTHON_BIN" "$ROOT/scripts/validate_arc_prize_submission.py" \
  "$ROOT/fixtures/kaggle_arc_format/submission.json"

echo "== Hard gate: AGI-3 fixture (top-score parquet) =="
"$PARQUET_PYTHON" "$ROOT/scripts/validate_arc_agi3_submission.py" \
  "$ROOT/fixtures/kaggle_arc_format/submission.parquet"

ARGS=(--root "$ROOT")
if [[ -n "$REPORT_DIR" ]]; then
  ARGS+=(--report-dir "$REPORT_DIR")
fi

echo "== Language-game local mastery (re-asserts hard gates on local artifacts) =="
export ARC_LOCAL_PYTHON="$PYTHON_BIN"
export ARC_LOCAL_PARQUET_PYTHON="$PARQUET_PYTHON"
exec "$PYTHON_BIN" "$ROOT/scripts/arc_local_mastery.py" "${ARGS[@]}"
