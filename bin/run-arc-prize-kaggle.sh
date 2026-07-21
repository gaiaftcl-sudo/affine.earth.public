#!/usr/bin/env bash
# Build and validate the exact ARC Prize submission.json contract offline.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT_DIR="${ARC_PRIZE_INPUT_DIR:-/kaggle/input/arc-prize-2026-arc-agi-3}"
OUTPUT_DIR="${ARC_PRIZE_OUTPUT_DIR:-$ROOT/reports/arc-prize-2026}"

usage() {
  cat <<'EOF'
Usage:
  bin/run-arc-prize-kaggle.sh [--input-dir DIR] [--output-dir DIR] [--push-notebook]

Builds only `submission.json` and validates every task has both mandatory
attempt_1 and attempt_2 grids. The default input directory is Kaggle's mounted
competition input. Kaggle notebook metadata has internet disabled.

--push-notebook requires KAGGLE_API_TOKEN or valid ~/.kaggle/kaggle.json.
It uploads the air-gapped notebook package; Kaggle membership rules still
control whether the competition input can be mounted and executed.
EOF
}

PUSH_NOTEBOOK=0
while (($#)); do
  case "$1" in
    --input-dir) INPUT_DIR="$2"; shift 2 ;;
    --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
    --push-notebook) PUSH_NOTEBOOK=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if ((PUSH_NOTEBOOK)); then
  command -v kaggle >/dev/null || { echo "Kaggle CLI is required." >&2; exit 127; }
  PUSH_LOG="$(mktemp)"
  trap 'rm -f "$PUSH_LOG"' EXIT
  kaggle kernels push -p "$ROOT/kaggle/arc-prize-2026" >"$PUSH_LOG" 2>&1 || {
    cat "$PUSH_LOG" >&2
    exit 1
  }
  cat "$PUSH_LOG"
  if rg --fixed-strings --quiet "Kernel push error:" "$PUSH_LOG"; then
    echo "Kaggle rejected the notebook package." >&2
    exit 1
  fi
  exit 0
fi

mkdir -p "$OUTPUT_DIR"
python3 "$ROOT/scripts/build_arc_prize_submission.py" \
  --input-dir "$INPUT_DIR" \
  --output-dir "$OUTPUT_DIR"
python3 "$ROOT/scripts/validate_arc_prize_submission.py" "$OUTPUT_DIR/submission.json"
