#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================================="
echo "  🚀 RUNNING FULL AFFINE.EARTH LLM & LLVM BENCHMARK TEST SUITE"
echo "  Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "========================================================================="
echo ""

echo "-------------------------------------------------------------------------"
echo "STEP 1: Running Automated Pytest Unit Tests..."
echo "-------------------------------------------------------------------------"
python3 -m pytest tests/ -v

echo ""
echo "-------------------------------------------------------------------------"
echo "STEP 2: Running Un-Flubbed Real Number Verification (Clang + Rational)..."
echo "-------------------------------------------------------------------------"
python3 scripts/verify_real_numbers_no_flub.py

echo ""
echo "-------------------------------------------------------------------------"
echo "STEP 3: Executing LLVM Clang Compiler Optimization Suite..."
echo "-------------------------------------------------------------------------"
python3 -m llm_llvm_bench.cli.main llvm run --opt-levels -O0,-O2,-O3,-Os --compiler clang --out reports/llvm_benchmark_live.json

echo ""
echo "-------------------------------------------------------------------------"
echo "STEP 4: Executing Domain Benchmark against Live https://affine.earth..."
echo "-------------------------------------------------------------------------"
python3 scripts/run_live_affine_earth_benchmark.py

echo ""
echo "========================================================================="
echo "  ✅ FULL BENCHMARK SUITE COMPLETE!"
echo "  Reports generated in: $SCRIPT_DIR/reports/"
echo "========================================================================="
