# LLVM / Clang Compiler Benchmark Suite

**Upstream reference:** [`https://github.com/llvm/llvm-test-suite`](https://github.com/llvm/llvm-test-suite)  
**In-repo runner:** `python3 -m llm_llvm_bench.cli.main llvm run`  
**Programs:** `llvm_micro_matrix_mul`, `llvm_codesize_sort` (`llm_llvm_bench/llvm/benchmarks.py`)  
**Proof script:** `scripts/verify_real_numbers_no_flub.py`

---

## 1. Execution commands

```bash
cd llm-llvm-benchmark-suite

# Full opt sweep → reports/llvm_benchmark_live.json
python3 -m llm_llvm_bench.cli.main llvm run \
  --opt-levels -O0,-O2,-O3,-Os \
  --compiler clang \
  --out reports/llvm_benchmark_live.json

# Compact proof receipt (different microbench printing PASS=10000)
python3 scripts/verify_real_numbers_no_flub.py
```

---

## 2. MEASURED — verify script Clang receipts (2026-07-20 22:14:57 UTC)

From `reports/real_verification_proof.json`:

| Opt Flag | Compile Time | Execution Wall-Time | `.text` Section | Total Binary | Program Verification |
|:---|---:|---:|---:|---:|:---|
| **`-O0`** | **97.119ms** | **71.315ms** | **16,384 B** | **33,624 B** | `PASS=10000` |
| **`-O2`** | **109.744ms** | **69.201ms** | **16,384 B** | **33,496 B** | `PASS=10000` |
| **`-O3`** | **100.603ms** | **67.760ms** | **16,384 B** | **33,496 B** | `PASS=10000` |
| **`-Os`** | **98.106ms** | **77.460ms** | **16,384 B** | **33,496 B** | `PASS=10000` |

---

## 3. MEASURED — CLI suite averages (matmul + sort)

| Opt | Avg Compile | Avg Exec | Total `.text` |
|:---|---:|---:|---:|
| `-O0` | 0.0957s | 0.0911s | 32,768 B |
| `-O2` | 0.1060s | 0.0631s | 32,768 B |
| `-O3` | 0.0962s | 0.0654s | 32,768 B |
| `-Os` | 0.0955s | 0.0790s | 32,768 B |

---

## 4. What each metric means

| Metric | Meaning |
|:---|:---|
| Compile time | Wall clock for `clang` invocation |
| Exec time | Wall clock running the produced binary |
| `.text` size | Code segment bytes from `size` |
| IR counts | Loads/stores/calls/vector ops/branches after compile |
| `PASS=10000` | Functional check for the verify-script microbench |

Interpretation guide: [Benchmarks](Benchmarks). Recipes: [Examples / Cookbook](Examples-Cookbook#4-llvm-suite--all-opt-levels).

---

## 5. Pytest coverage

`tests/test_llvm.py` compiles and runs the package microbench via `LLVMDriver` / `LLVMRunner` (real clang). Part of the **10 passed** suite.
