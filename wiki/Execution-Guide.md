# Single-Command Benchmark Rerun Execution Guide

To rerun the full benchmark suite against `https://affine.earth` on command:

```bash
cd llm-llvm-benchmark-suite
./bin/run-full-benchmark.sh
```

---

## What the Script Executes:

1. **Step 1: Pytest Unit Test Suite**  
   Runs `python3 -m pytest tests/ -v` (10/10 passed).

2. **Step 2: Un-Flubbed Real Number Verification**  
   Runs `python3 scripts/verify_real_numbers_no_flub.py`, performing live Clang builds (`-O0`, `-O2`, `-O3`, `-Os`), 10,000 rational additions, and live HTTP endpoint probes.

3. **Step 3: LLVM Clang Compiler Suite**  
   Runs `python3 -m llm_llvm_bench.cli.main llvm run --opt-levels -O0,-O2,-O3,-Os --compiler clang`.

4. **Step 4: Domain Benchmark against Live Endpoint**  
   Runs `python3 scripts/run_live_affine_earth_benchmark.py`, evaluating live responses against `https://affine.earth/language-invariant/healthz` and writing fresh report outputs in `reports/`.
