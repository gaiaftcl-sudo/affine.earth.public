#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

live=0
if [[ "${1:-}" == "--live" ]]; then
  live=1
elif [[ $# -ne 0 ]]; then
  echo "Usage: $0 [--live]" >&2
  exit 2
fi

mkdir -p reports
./bin/verify-rig.sh

compiler="${AFFINE_LLVM_COMPILER:-clang}"
opt_levels="${AFFINE_LLVM_OPT_LEVELS:--O0,-O2,-O3,-Os}"
python3 -m llm_llvm_bench.cli.main llvm run \
  --compiler "$compiler" \
  --opt-levels "$opt_levels" \
  --out reports/llvm_benchmark.json

if [[ "$live" -eq 1 ]]; then
  : "${AFFINE_ENDPOINT:?Set AFFINE_ENDPOINT (see configs/affine-earth.env.example).}"
  : "${AFFINE_MODEL:?Set AFFINE_MODEL (see configs/affine-earth.env.example).}"
  python3 scripts/run_live_affine_earth_benchmark.py --out reports/llm_benchmark.json
fi

echo "Completed MEASURED local benchmark run. Reports: $SCRIPT_DIR/reports/"
