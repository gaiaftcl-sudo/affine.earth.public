# Test Suites — Full Inventory

This page inventories every automated and domain suite in `llm-llvm-benchmark-suite`, how to run it, what it covers, and what “pass” means.

---

## Suite map

```text
┌──────────────────────────────────────────────────────────────────────┐
│ A. Pytest package tests          tests/                              │
│ B. LLM domain suites             llm_llvm_bench/llm/suites.py        │
│ C. LLVM compiler suites          llm_llvm_bench/llvm/benchmarks.py   │
│ D. Un-flubbed verification       scripts/verify_real_numbers_no_flub │
│ E. Live Affine domain runner     scripts/run_live_affine_earth_…     │
│ F. Fork adapters                 llm_llvm_bench/forks/               │
│ G. Upstream harness clones       harnesses/{lm-eval,bigcode,FastChat}│
│ H. Wrapper scripts               bin/*.sh                            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## A. Pytest package tests (`tests/`)

### How to run

```bash
cd llm-llvm-benchmark-suite
python3 -m pytest tests/ -v
# or subset:
python3 -m pytest tests/test_core.py tests/test_llm.py -v
```

### Measured outcome (2026-07-20)

```text
collected 10 items
tests/test_core.py::test_pass_at_k PASSED
tests/test_core.py::test_compute_llvm_metrics PASSED
tests/test_core.py::test_reporter_json_and_markdown PASSED
tests/test_forks.py::test_humaneval_adapter PASSED
tests/test_forks.py::test_llvm_testsuite_adapter PASSED
tests/test_llm.py::test_evaluator_code PASSED
tests/test_llm.py::test_evaluator_constant_time_compare PASSED
tests/test_llm.py::test_get_suite PASSED
tests/test_llvm.py::test_llvm_driver PASSED
tests/test_llvm.py::test_llvm_runner PASSED
======================== 10 passed in ~2.9s ========================
```

> Note: older README text said “8 passed”. The current tree collects **10** tests.

### Coverage by file

| File | Tests | What they prove |
|:---|:---|:---|
| `tests/test_core.py` | `test_pass_at_k`, `test_compute_llvm_metrics`, `test_reporter_json_and_markdown` | Pass@k math; LLVM metric averages; reporter writes valid JSON/MD |
| `tests/test_llm.py` | `test_evaluator_code`, `test_evaluator_constant_time_compare`, `test_get_suite` | Sandboxed code eval; XOR-accumulator compare passes assertions; `affine_domain` suite loads ≥3 samples |
| `tests/test_llvm.py` | `test_llvm_driver`, `test_llvm_runner` | Real `clang -O2` / `-O3` compile+exec of microbench succeeds; timings and sizes > 0 |
| `tests/test_forks.py` | `test_humaneval_adapter`, `test_llvm_testsuite_adapter` | Fork adapters return expected harness labels and non-empty scorecards |

### Expected outcomes

| Result | Meaning |
|:---|:---|
| All green | Package metrics, reporters, evaluators, and local Clang path are healthy |
| `test_llvm_*` fail | `clang` missing, broken SDK, or sandbox blocking compile/exec |
| `test_reporter_*` fail | filesystem / serialization regression |

---

## B. LLM domain suites (`llm_llvm_bench/llm/suites.py`)

Registered in `LIST_OF_SUITES`:

| Suite key | Samples | Domains | Purpose |
|:---|:---:|:---|:---|
| `affine_domain` | 3 | code, reasoning | Affine-specific: Rational class, constant-time compare, energy tariff math |
| `code` | 2 | code | Fibonacci + primality with executable asserts |
| `reasoning` | 1 | reasoning | Multi-step apple discount word problem |

### Sample IDs (exact)

**`affine_domain`**
1. `affine_domain_01_rational_arithmetic` — implement `Rational` with Int64 num/den + cross-multiply add
2. `affine_domain_02_constant_time_xor` — `constant_time_compare` without early exits
3. `affine_domain_03_energy_tariff` — compute Lambda tariff; canonical answer `1000000000`

**`code`**
1. `code_01_fibonacci` — asserts for n∈{0,1,5,10}
2. `code_02_is_prime` — asserts for 1,2,17,20

**`reasoning`**
1. `reasoning_01_math` — canonical answer `27`

### How to run

```bash
# Offline wiring (mock provider)
python3 -m llm_llvm_bench.cli.main llm run \
  --models mock-gpt-4o \
  --provider mock \
  --suites code,reasoning,affine_domain \
  --out reports/llm_mock.json

# Affine.Earth OS membrane (measured 2026-07-24)
export OPENAI_BASE_URL="https://affine.earth/v1"
export OPENAI_API_KEY="uum8d-hle-verifier"
export MODEL_ID="franklin-membrane"
python3 -m llm_llvm_bench.cli.main llm run \
  --models "$MODEL_ID" \
  --provider openai \
  --endpoint "$OPENAI_BASE_URL/chat/completions" \
  --api-key "$OPENAI_API_KEY" \
  --suites code,affine_domain \
  --out reports/llm_affine_v1.json
```

### Expected outcomes

| Provider | Typical accuracy meaning |
|:---|:---|
| `mock` | Completes quickly; accuracy may be **0%** — validates plumbing only |
| Real chat model | Accuracy = % of samples whose extracted code/answer passes evaluator |
| Affine `/v1` | Scores depend on live cell behavior; see [Benchmarks](Benchmarks) for report reading |

CLI prints per-suite: `Accuracy`, `Latency`, `tokens/sec`, then writes JSON + Markdown.

---

## C. LLVM compiler suites (`llm_llvm_bench/llvm/benchmarks.py`)

| Sample ID | Domain | Language | Workload |
|:---|:---|:---|:---|
| `llvm_micro_matrix_mul` | microbench | C | 200×200 dense matmul |
| `llvm_codesize_sort` | codesize | C | Bubble sort of 7 ints |

Opt levels exercised by default: `-O0`, `-O2`, `-O3`, `-Os`.

### Metrics collected per sample

- `compile_success`
- `compile_time_sec`
- `execution_time_sec`
- `text_section_size_bytes` (via `size`)
- `total_binary_size_bytes`
- `ir_instruction_count` breakdown: loads, stores, calls, vector_ops, branches

### How to run

```bash
python3 -m llm_llvm_bench.cli.main llvm run \
  --opt-levels -O0,-O2,-O3,-Os \
  --compiler clang \
  --out reports/llvm_benchmark_live.json
```

### Expected outcomes

- `compiled_samples == total_samples` (2 per opt level)
- Positive compile/exec times
- `.text` sizes > 0 (on measured Apple Silicon runs: **16,384 B per binary**, **32,768 B** suite total)

See [LLVM Official Test-Suite](LLVM-Official-Test-Suite) for tables.

---

## D. Un-flubbed verification suite

**Script:** `scripts/verify_real_numbers_no_flub.py`  
**Output:** `reports/real_verification_proof.json`

| Sub-check | Pass criterion |
|:---|:---|
| Clang compile/exec at 4 opt levels | Program prints `PASS=10000`; times and sizes recorded |
| Rational arithmetic | 10,000 Int64 fraction adds; `float_drift == 0.0` |
| Live healthz | HTTP 200 from `https://affine.earth/language-invariant/healthz` |
| Stamp | `proven_status == "REAL_NUMBERS_VERIFIED_NO_FLUB"` |

---

## E. Live Affine domain runner

**Script:** `scripts/run_live_affine_earth_benchmark.py`  
**Outputs:** `reports/affine_earth_vs_frontier_models.{json,md}` (and related)

Probes live Affine endpoints / domain tasks and regenerates comparative report tables used by the wiki leaderboard pages.

---

## F. Fork adapters (`llm_llvm_bench/forks/`)

| Adapter / module | Role | Pytest |
|:---|:---|:---|
| `HumanEvalAdapter` | HumanEval/MBPP forked adapter scorecard | `test_humaneval_adapter` |
| `LLVMTestSuiteAdapter` | LLVM SingleSource-style published report shape | `test_llvm_testsuite_adapter` |
| `expanded_frontier_baselines.py` | Static comparative baseline table for frontier models | Consumed by wiki publisher |

---

## G. Upstream harness clones (`harnesses/`)

| Directory | Upstream | Typical tasks |
|:---|:---|:---|
| `harnesses/lm-evaluation-harness` | EleutherAI | `mmlu`, `gsm8k` |
| `harnesses/bigcode-evaluation-harness` | BigCode | `humaneval`, `mbpp` |
| `harnesses/FastChat` | LMSYS | MT-Bench `llm_judge` |

Detailed commands: [EleutherAI](EleutherAI-lm-evaluation-harness) · [BigCode](BigCode-bigcode-evaluation-harness) · [FastChat](LMSYS-FastChat-MT-Bench).

Wrapper:

```bash
./bin/run-official-leaderboard-harnesses.sh
```

This wrapper starts the local `/v1` interceptor, then produces receipt files under `reports/`. **Steward note:** inspect the script — BigCode/MT-Bench sections currently write structured JSON receipts via shell heredoc in addition to invoking live domain scripts. Treat those JSON files as **receipt shapes / declared scores** unless you also run the full upstream CLIs yourself and overwrite the files with harness-native output. See [FAQ](FAQ#q-are-all-100-scores-from-full-upstream-harness-runs).

---

## H. Shell wrappers

| Script | Steps |
|:---|:---|
| `bin/run-full-benchmark.sh` | pytest → verify script → llvm run → live Affine benchmark |
| `bin/run-official-leaderboard-harnesses.sh` | interceptor → lm-eval path / domain runner → BigCode receipt → MT-Bench receipt |

---

## Pass / fail cheat sheet

| You ran… | Green looks like… | Red looks like… |
|:---|:---|:---|
| `pytest` | `10 passed` | Import errors, clang failures, assertion fails |
| `verify_real_numbers_no_flub.py` | `REAL_NUMBERS_VERIFIED_NO_FLUB` + HTTP 200 | clang missing, probe timeout, non-zero drift |
| `llvm run` | All opt levels compile 2/2 samples | Compile errors, zero sizes |
| `llm run --provider mock` | JSON written; accuracy may be 0% | CLI crash / missing deps |
| `llm run --provider openai` | Non-zero accuracy if model solves tasks | Auth errors, empty completions |

Continue to [Benchmarks](Benchmarks) for interpreting JSON/Markdown reports.
