# Getting Started

This guide gets you from zero to a verified local run of the Affine.Earth public benchmark suite.

**Repository:** [`https://github.com/gaiaftcl-sudo/affine.earth.public`](https://github.com/gaiaftcl-sudo/affine.earth.public)  
**Package directory:** `llm-llvm-benchmark-suite/`

---

## 0. Create an Affine.Earth account (required for live third-party runs)

**Outsiders: do this first** before claiming a live Affine session or upstream harness score against Affine.Earth.

Affine.Earth uses **Sovereign entry** (BTC edge wallet), not email/password. Full UI path, screenshots, blockers, and smoke checks:

→ **[Create Account / Signup](Create-Account-Signup)**

Minimum gate:

1. Open `https://affine.earth` → `/language-game/`
2. **New wallet** → consent → **Create wallet + QFOT** (or **Returning** with an address you control)
3. **Export private key** and store it offline
4. Confirm your intended `/v1` (or other) endpoint returns real API JSON before harness scoring — see blockers on the Signup page
5. Smoke the signup surface without creating users: `python3 scripts/check_affine_signup_surface.py`

Local-only Clang / pytest / mock-provider work does not require an Affine account.

---

## 1. Prerequisites

| Requirement | Notes |
|:---|:---|
| Python **3.9+** | Verified with CPython 3.9.6 on macOS |
| `pip` | For editable install |
| `clang` on `PATH` | Required for LLVM suites and `verify_real_numbers_no_flub.py` |
| `size` (binutils / Xcode CLI) | Used to read `.text` section bytes |
| Network (optional) | Needed only for live `affine.earth` probes and remote LLM providers |

Check tools:

```bash
python3 --version
clang --version
which size
```

---

## 2. Clone and install

```bash
git clone https://github.com/gaiaftcl-sudo/affine.earth.public.git
cd affine.earth.public/llm-llvm-benchmark-suite
pip install -e .
```

Editable install exposes the console entrypoint `llm-llvm-bench` (from `pyproject.toml` → `llm_llvm_bench.cli.main:cli`). You can also invoke:

```bash
python3 -m llm_llvm_bench.cli.main --help
```

Expected top-level commands:

```text
Commands:
  llm    LLM Evaluation Commands
  llvm   LLVM Compiler Benchmark Commands
  serve  Launch interactive LLM & LLVM benchmark web dashboard
```

---

## 3. First verification (offline-capable core)

### 3a. Pytest (must pass)

```bash
python3 -m pytest tests/ -v
```

**Measured on 2026-07-20:** `10 passed` in ~2.9s.

Tests cover:

- Core metrics (`pass@k`, LLVM metric aggregation, JSON/Markdown reporter)
- LLM evaluator (code execution + constant-time compare)
- Suite loading (`affine_domain`)
- LLVM driver + runner (real `clang`)
- Fork adapters (HumanEval / LLVM test-suite adapters)

### 3b. Un-flubbed real-number verification

```bash
python3 scripts/verify_real_numbers_no_flub.py
```

This script:

1. Compiles and runs a C microbenchmark with `clang` at `-O0`, `-O2`, `-O3`, `-Os`
2. Performs 10,000 exact rational additions (no float path)
3. Probes `https://affine.earth/language-invariant/healthz`
4. Writes `reports/real_verification_proof.json`

**Measured receipt fields (2026-07-20 22:14:57 UTC):**

| Field | Value |
|:---|:---|
| `rational_arithmetic_real_metrics.float_drift` | `0.0` |
| `rational_arithmetic_real_metrics.iterations` | `10000` |
| `live_probe_metrics.status_code` | `200` |
| `live_probe_metrics.latency_ms` | `277.27` |
| `proven_status` | `REAL_NUMBERS_VERIFIED_NO_FLUB` |

---

## 4. Environment variables (remote LLM / harness routing)

For OpenAI-compatible providers or Affine `/v1` routing:

```bash
export OPENAI_API_KEY="uum8d-public-verifier"   # or your provider key
export OPENAI_BASE_URL="http://affine.earth/v1" # or http://127.0.0.1:8000/v1 for local interceptor
```

The local wire-frame interceptor can be started with:

```bash
python3 llm_llvm_bench/server/affine_v1_interceptor.py 8000
```

The official harness wrapper sets `OPENAI_BASE_URL=http://127.0.0.1:8000/v1` automatically:

```bash
./bin/run-official-leaderboard-harnesses.sh
```

---

## 5. First LLM and LLVM CLI runs

### Offline mock LLM wiring check

```bash
python3 -m llm_llvm_bench.cli.main llm run \
  --models mock-gpt-4o \
  --provider mock \
  --suites code,reasoning,affine_domain \
  --out reports/llm_mock_smoke.json
```

**Measured on 2026-07-20:** the mock provider completed all suites and wrote JSON/MD reports. Accuracy was **0.0%** because the mock completions are not solution-correct — this is a **wiring smoke test**, not a model quality claim. Use a real provider for accuracy scores.

### Real Clang LLVM suite

```bash
python3 -m llm_llvm_bench.cli.main llvm run \
  --opt-levels -O0,-O2,-O3,-Os \
  --compiler clang \
  --out reports/llvm_benchmark_live.json
```

**Measured markdown summary (2026-07-20):**

| Opt | Avg Compile | Avg Exec | Text Size (2 programs) |
|:---|:---|:---|:---|
| `-O0` | 0.0957s | 0.0911s | 32,768 B |
| `-O2` | 0.1060s | 0.0631s | 32,768 B |
| `-O3` | 0.0962s | 0.0654s | 32,768 B |
| `-Os` | 0.0955s | 0.0790s | 32,768 B |

---

## 6. One-command full suite

```bash
./bin/run-full-benchmark.sh
```

Runs, in order:

1. `pytest tests/ -v`
2. `scripts/verify_real_numbers_no_flub.py`
3. `llvm run` → `reports/llvm_benchmark_live.json`
4. `scripts/run_live_affine_earth_benchmark.py` → comparative reports under `reports/`

---

## 7. Local web dashboard

```bash
python3 -m llm_llvm_bench.cli.main serve --port 8888
# open http://127.0.0.1:8888
```

---

## 8. Where outputs land

| Path | Contents |
|:---|:---|
| `reports/real_verification_proof.json` | Clang + rational + healthz proof |
| `reports/llvm_benchmark_live.json` / `.md` | Full LLVM CLI report |
| `reports/affine_earth_vs_frontier_models.json` / `.md` | Domain vs frontier comparison table |
| `reports/affine-bigcode-results.json` | BigCode receipt shape |
| `reports/affine-mt-bench-results.json` | MT-Bench receipt shape |
| `reports/affine-results/` | lm-eval style output directory |

Next: [Test Suites](Test-Suites) · [Benchmarks](Benchmarks) · [Examples / Cookbook](Examples-Cookbook) · [FAQ](FAQ)
