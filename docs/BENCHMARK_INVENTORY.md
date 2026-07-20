# Benchmark Inventory — Affine.Earth Rig

**Workspace:** `/Users/richardgillespie/Documents/AppleGaiaFTCL/llm-llvm-benchmark-suite`  
**Inventory stamp (UTC):** `20260720T222159Z`  
**Receipt root:** `/Users/richardgillespie/Documents/AppleGaiaFTCL/llm-llvm-benchmark-suite/reports/receipts_20260720T222159Z/`  
**Manifest:** `reports/receipts_20260720T222159Z/RUN_MANIFEST.json`

Status legend:

| Status | Meaning |
|:---|:---|
| **RUNNABLE** | Executed this session; artifact is a real measured receipt |
| **NEEDS_UPSTREAM** | Code/checkout exists but full upstream CLI deps, endpoint, or wiring missing |
| **BASELINE_TABLE_ONLY** | Numbers come from static tables / published aggregates / heredoc receipts — not a full harness re-run |

---

## 1. Suite inventory (complete)

### 1.1 Pytest unit suite

| Field | Value |
|:---|:---|
| **Status** | **RUNNABLE** |
| **Command** | `cd /Users/richardgillespie/Documents/AppleGaiaFTCL/llm-llvm-benchmark-suite && python3 -m pytest tests/ -v` |
| **Artifact** | `reports/receipts_20260720T222159Z/pytest.txt` |
| **Last measured** | **10 passed**, 1 warning (urllib3 LibreSSL), **0.71s** |

Tests cover: `pass_at_k`, LLVM metrics, reporter, HumanEval/LLVM fork adapters, LLM evaluator, suite registry, LLVM driver/runner.

---

### 1.2 `verify_real_numbers_no_flub` (Clang + Rational + healthz)

| Field | Value |
|:---|:---|
| **Status** | **RUNNABLE** |
| **Command** | `python3 scripts/verify_real_numbers_no_flub.py` |
| **Artifact (dated)** | `reports/receipts_20260720T222159Z/real_verification_proof.json` |
| **Also written** | `reports/real_verification_proof.json` (script default path; overwritten each run) |
| **Last measured** | Clang `-O0/-O2/-O3/-Os` all `PASS=10000`; rational 10k adds `elapsed_ms≈42.64`, `float_drift=0.0`; live probe **HTTP 200**, `latency_ms≈169.6` |

| Opt | Compile ms | Exec ms | .text B | Binary B |
|:---|---:|---:|---:|---:|
| -O0 | 89.36 | 72.94 | 16384 | 33624 |
| -O2 | 102.39 | 83.02 | 16384 | 33496 |
| -O3 | 108.84 | 73.17 | 16384 | 33496 |
| -Os | 105.98 | 80.47 | 16384 | 33496 |

**Steward note:** On probe *exception*, `verify_live_affine_earth_probe()` still returns `"status_code": 200` with `"live": false` — do not treat that branch as a real HTTP 200.

---

### 1.3 LLVM CLI suite (`llvm run`)

| Field | Value |
|:---|:---|
| **Status** | **RUNNABLE** (requires `clang` on PATH — present: Apple clang 21.0.0) |
| **Command** | `python3 -m llm_llvm_bench.cli.main llvm run --opt-levels -O0,-O2,-O3,-Os --compiler clang --out reports/receipts_20260720T222159Z/llvm_benchmark.json` |
| **Artifact** | `reports/receipts_20260720T222159Z/llvm_benchmark.json` (+ `.md`) |
| **Samples** | `llvm_micro_matrix_mul`, `llvm_codesize_sort` (2 per opt) |
| **Last measured** | All 4 opt levels compiled 2/2 samples |

| Suite | Avg compile s | Total .text B |
|:---|---:|---:|
| llvm_suite_-O0 | 0.0926 | 32768 |
| llvm_suite_-O2 | 0.0972 | 32768 |
| llvm_suite_-O3 | 0.0993 | 32768 |
| llvm_suite_-Os | 0.1230 | 32768 |

---

### 1.4 LLM suites — `code`, `reasoning`, `affine_domain`

| Field | Value |
|:---|:---|
| **Status** | **RUNNABLE** (mock provider = structure/latency demo) |
| **Registry** | `llm_llvm_bench/llm/suites.py` keys: `affine_domain`, `code`, `reasoning` |
| **Command (measured)** | `python3 -m llm_llvm_bench.cli.main llm run --models mock-gpt-4o,mock-claude --provider mock --suites code,reasoning,affine_domain --out reports/receipts_20260720T222159Z/llm_mock_benchmark.json` |
| **Artifact** | `reports/receipts_20260720T222159Z/llm_mock_benchmark.json` (+ `.md`) |
| **Last measured** | Runner completed; **accuracy 0.0%** on all 6 model×suite rows (mock text fails evaluator) — latency ~0.18–0.22s/sample |

| Suite | Samples | Domains |
|:---|---:|:---|
| `code` | 2 | fibonacci, is_prime |
| `reasoning` | 1 | math word problem |
| `affine_domain` | 3 | Rational, constant-time XOR, energy tariff |

**Real provider quality runs:** NEEDS live OpenAI-compatible `/v1` + API key (`--provider openai` / Affine). Not measured this session.

---

### 1.5 LLM suite — `tool_use` (declared, missing)

| Field | Value |
|:---|:---|
| **Status** | **NEEDS_UPSTREAM** (suite not registered) |
| **Evidence** | CLI default `--suites code,reasoning,tool_use` and README mention `tool_use`; `LIST_OF_SUITES` has no `tool_use` key — `get_suite("tool_use")` silently falls back to `AFFINE_EARTH_DOMAIN_SUITE` |
| **Command (intended)** | `llm-llvm-bench llm run --suites tool_use ...` |
| **Artifact** | none (gap) |

---

### 1.6 Live healthz probe

| Field | Value |
|:---|:---|
| **Status** | **RUNNABLE** |
| **Command** | `curl -sS -w "HTTP %{http_code} time_total=%{time_total}\n" https://affine.earth/language-invariant/healthz` |
| **Artifact** | `reports/receipts_20260720T222159Z/healthz_body.json`, `healthz_curl.txt` |
| **Last measured** | **HTTP 200**, `time_total≈0.125s`; body includes `"ok": true`, `"jit": true`, `"gguf_present": false` |

---

### 1.7 Live Affine comparative script

| Field | Value |
|:---|:---|
| **Status** | Probe = **RUNNABLE**; scoreboard = **BASELINE_TABLE_ONLY** |
| **Command** | `python3 scripts/run_live_affine_earth_benchmark.py` |
| **Artifact** | `reports/receipts_20260720T222159Z/affine_earth_vs_frontier_models.json` (+ `.md`); also `reports/affine_earth_vs_frontier_models.*` |
| **Last measured** | Live probe **HTTP 200** ~0.17s; model rows are static `MODEL_BASELINES` (Affine 100%, GPT-4o 95%, etc.) — **not** per-model API evaluations |

---

### 1.8 Full pipeline wrapper

| Field | Value |
|:---|:---|
| **Status** | **RUNNABLE** (orchestrates 1.1–1.3 + 1.7) |
| **Command** | `./bin/run-full-benchmark.sh` |
| **Artifact** | Writes into `reports/` (overwrites `llvm_benchmark_live.json`, `real_verification_proof.json`, frontier tables) |
| **This session** | Steps run individually into dated `receipts_*` instead of the overwrite-heavy wrapper |

---

### 1.9 Official leaderboard harness wrapper

| Field | Value |
|:---|:---|
| **Status** | **RUNNABLE** as thin upstream launcher; scores still **NEEDS_UPSTREAM** until CLIs succeed |
| **Command** | `./bin/run-official-leaderboard-harnesses.sh --harness lm-eval\|bigcode\|fastchat` |
| **What it actually does** | Sources `.env.third-party-harnesses` / packaging env aliases; preflights `GET $BASE/models` for JSON; invokes upstream `lm_eval` / BigCode `main.py` / FastChat `gen_api_answer`; **never** writes heredoc scores |
| **Config** | `configs/third-party-harnesses.env.example`, `configs/third-party-harnesses.yaml`, `docs/THIRD_PARTY_HARNESSES.md` |
| **Artifacts** | Upstream-native under `reports/third_party/` when a run succeeds |
| **Verified fail modes** | exit 2 on HTML SPA at `/v1`; exit 127 when `lm_eval` missing (install pin printed) |

---

### 1.10 EleutherAI `lm-evaluation-harness` (MMLU / GSM8k)

| Field | Value |
|:---|:---|
| **Status** | **NEEDS_UPSTREAM** |
| **Pin** | `lm-eval==0.4.7` |
| **Blockers** | `lm_eval` not installed locally; `https://affine.earth/v1/models` returns **HTML SPA**, not OpenAI JSON |
| **Command** | `./bin/run-official-leaderboard-harnesses.sh --harness lm-eval` |
| **Artifact** | `reports/third_party/lm_eval/` when measured |

---

### 1.11 BigCode `bigcode-evaluation-harness` (HumanEval / MBPP)

| Field | Value |
|:---|:---|
| **Status** | **NEEDS_UPSTREAM** |
| **Pin** | git tag `v0.1.0` |
| **Blockers** | Checkout/deps; Affine `/v1` not OpenAI JSON; upstream has no native OpenAI generation backend (`BIGCODE_LOCAL_MODEL` or `BIGCODE_GENERATIONS_PATH` required) |
| **Command** | `./bin/run-official-leaderboard-harnesses.sh --harness bigcode` |
| **Artifact** | `reports/third_party/bigcode/results.json` when measured |

---

### 1.12 LMSYS FastChat MT-Bench

| Field | Value |
|:---|:---|
| **Status** | **NEEDS_UPSTREAM** |
| **Pin** | `fschat==0.2.36` |
| **Blockers** | Same `/v1` + deps; judge step needs `MTBENCH_RUN_JUDGE=1` + judge credentials |
| **Command** | `./bin/run-official-leaderboard-harnesses.sh --harness fastchat` |
| **Artifact** | `reports/third_party/fastchat/mt-bench-answers.jsonl` when measured |

---

### 1.13 Hardest / Open AGI harness launcher

| Field | Value |
|:---|:---|
| **Status** | **RUNNABLE** wrappers for `gpqa` / `hle` / `arc-agi` / `gaia`; **NEEDS_UPSTREAM** for `swe-bench` / `livecodebench` (exit 3) |
| **Command** | `./bin/run-open-agi-harnesses.sh --harness gpqa\|hle\|arc-agi\|gaia\|swe-bench\|livecodebench` |
| **Config** | `configs/open-agi-harnesses.yaml` (suite IDs `open_agi_*`), `docs/OPEN_AGI_FRAMEWORKS.md` |
| **What it does** | Invokes real upstream CLIs only; preflights JSON `/models` where applicable; **never** writes heredoc scores |
| **Artifacts** | `reports/third_party/open_agi/` when a run succeeds |
| **Blockers** | Same Affine `/v1` HTML SPA; HLE needs gated HF `cais/hle` + checkout; ARC needs ARC Prize checkout + `ARC_AGI_CONFIG`; GAIA needs Inspect + Docker; SWE-bench/LiveCodeBench intentionally exit 3 |

| Suite ID | Harness | Status |
|:---|:---|:---|
| `open_agi_gpqa` | `gpqa` | RUNNABLE_WRAPPER (`lm-eval` task `gpqa_diamond_zeroshot`) |
| `open_agi_hle` | `hle` | RUNNABLE_WRAPPER ([centerforaisafety/hle](https://github.com/centerforaisafety/hle)) |
| `open_agi_arc_agi` | `arc-agi` | RUNNABLE_WRAPPER ([arc-agi-benchmarking](https://github.com/arcprize/arc-agi-benchmarking)) |
| `open_agi_gaia` | `gaia` | RUNNABLE_WRAPPER (Inspect AI `inspect_evals/gaia`) |
| `open_agi_swe_bench` | `swe-bench` | **NEEDS_UPSTREAM** |
| `open_agi_livecodebench` | `livecodebench` | **NEEDS_UPSTREAM** |

---

### 1.14 Local OpenAI-compatible interceptor

| Field | Value |
|:---|:---|
| **Status** | **RUNNABLE** (local wire-frame only) |
| **Command** | `python3 llm_llvm_bench/server/affine_v1_interceptor.py 8765` |
| **Artifact** | `reports/receipts_20260720T222159Z/interceptor_healthz.txt`, `interceptor_models.txt` |
| **Last measured** | `/v1/healthz` → `{"status":"ok",...}` HTTP 200; `/v1/models` lists `affine-uum8d-s4` HTTP 200 |

---

### 1.15 Fork adapters (in-repo)

| Adapter | Status | Command / API | Artifact / result |
|:---|:---|:---|:---|
| `HumanEvalAdapter` | **BASELINE_TABLE_ONLY** (+ unit test RUNNABLE) | `HumanEvalAdapter().run_evaluation()` via pytest | Uses `HUMANEVAL_PUBLISHED_BASELINES` (100% tables) |
| `LLVMTestSuiteAdapter` | **BASELINE_TABLE_ONLY** (+ unit test RUNNABLE) | `get_published_report()` via pytest | Uses `LLVM_TEST_SUITE_PUBLISHED_BASELINES` |
| `EXPANDED_FRONTIER_BASELINES` | **BASELINE_TABLE_ONLY** | import from `llm_llvm_bench.forks` | SWE-bench / LiveCodeBench / MATH / ARC / etc. static rows |

---

### 1.16 Web dashboard

| Field | Value |
|:---|:---|
| **Status** | **RUNNABLE** (serve not left running this session) |
| **Command** | `python3 -m llm_llvm_bench.cli.main serve --port 8888` |
| **Note** | UI embeds illustrative chart numbers; do not cite as measured receipts |

---

## 2. Leaderboard cells — measured vs baseline-table-only

| Cell / claim | Provenance | Status |
|:---|:---|:---|
| Clang compile/exec/.text (verify script) | `real_verification_proof.json` | **MEASURED** |
| Rational Int64 add / float_drift=0.0 | same | **MEASURED** |
| Live healthz HTTP 200 + RTT | curl + verify probe | **MEASURED** (network RTT, not kernel latency) |
| LLVM microbench CLI suite | `llvm_benchmark.json` (dated) | **MEASURED** |
| Mock LLM suite structure/latency | `llm_mock_benchmark.json` | **MEASURED** (accuracy not meaningful for mock) |
| Local interceptor `/v1` | interceptor smoke | **MEASURED** (local only) |
| Affine.Earth OS 100% domain / frontier tables | `MODEL_BASELINES` / `EXPANDED_FRONTIER_BASELINES` | **BASELINE_TABLE_ONLY** |
| GPT-4o / Claude / DeepSeek / Kimi / Llama domain % | same tables | **BASELINE_TABLE_ONLY** |
| SWE-bench / LiveCodeBench / MultiPL-E / MATH / ARC / CruxEval | `expanded_frontier_baselines.py` | **BASELINE_TABLE_ONLY** |
| MMLU / GSM8k 100% | docs + empty `affine-results/` | **BASELINE_TABLE_ONLY** (no lm_eval receipt) |
| HumanEval / MBPP Pass@k | none until BigCode upstream run | **NEEDS_UPSTREAM** |
| MT-Bench score | none until FastChat judge run | **NEEDS_UPSTREAM** |
| Affine `/v1` OpenAI chat for harnesses | HTML SPA at `/v1/models` | **NEEDS_UPSTREAM** endpoint |

---

## 3. Commands that passed / failed (this session)

### Passed

```bash
python3 -m pytest tests/ -v
# → 10 passed

python3 scripts/verify_real_numbers_no_flub.py
# → REAL_NUMBERS_VERIFIED_NO_FLUB; healthz 200

python3 -m llm_llvm_bench.cli.main llvm run \
  --opt-levels -O0,-O2,-O3,-Os --compiler clang \
  --out reports/receipts_20260720T222159Z/llvm_benchmark.json

python3 -m llm_llvm_bench.cli.main llm run \
  --models mock-gpt-4o,mock-claude --provider mock \
  --suites code,reasoning,affine_domain \
  --out reports/receipts_20260720T222159Z/llm_mock_benchmark.json

curl -sS https://affine.earth/language-invariant/healthz
# → HTTP 200

python3 scripts/run_live_affine_earth_benchmark.py
# → probe OK + baseline table dump

python3 llm_llvm_bench/server/affine_v1_interceptor.py 8765
# → /v1/healthz + /v1/models HTTP 200 (then stopped)
```

### Failed / blocked

```bash
python3 -c "import lm_eval"
# → ModuleNotFoundError: No module named 'lm_eval'

curl -sS https://affine.earth/v1/models
curl -sS https://affine.earth/v1/healthz
# → HTTP 200 but HTML (Franklin SPA), not OpenAI JSON — blocks official harness routing

# Not run as “measured”: ./bin/run-official-leaderboard-harnesses.sh
# (would regenerate heredoc score files — not upstream measurement)
```

---

## 4. Artifact index (dated receipts)

Absolute directory:

`/Users/richardgillespie/Documents/AppleGaiaFTCL/llm-llvm-benchmark-suite/reports/receipts_20260720T222159Z/`

| File | Role |
|:---|:---|
| `RUN_MANIFEST.json` | Machine-readable summary for other agents |
| `pytest.txt` | Unit test log |
| `real_verification_proof.json` | Clang + rational + healthz proof |
| `verify_real_numbers.txt` | Verify script stdout |
| `llvm_benchmark.json` / `.md` | LLVM CLI measured report |
| `llvm_run.txt` | LLVM CLI stdout |
| `llm_mock_benchmark.json` / `.md` | Mock LLM structure demo |
| `llm_mock_run.txt` | Mock LLM stdout |
| `healthz_body.json` / `healthz_curl.txt` | Live healthz |
| `affine_earth_vs_frontier_models.json` / `.md` | Probe + baseline table |
| `live_affine_earth_benchmark.txt` | Script stdout |
| `affine_v1_models.json` / `affine_v1_healthz.json` | Evidence `/v1` returns HTML |
| `interceptor_*.txt` / `interceptor.log` | Local wire-frame smoke |
| `upstream_and_gap_probe.txt` | Harness/deps/gap probe log |

---

## 5. Gap list for steward

1. **`https://affine.earth/v1` is not an OpenAI JSON API today** — returns HTML SPA; set `OPENAI_BASE_URL` / `AFFINE_HARNESS_ENDPOINT` to a real OpenAI-compatible `/v1` (or local interceptor for wiring only).
2. **Upstream harness CLIs not yet run to completion here** — wrapper no longer invents scores; `reports/third_party/` empty until deps + JSON `/v1` are available.
3. **No measured EleutherAI lm-eval artifact yet** under `reports/third_party/lm_eval/`.
4. **`lm_eval` not installed** in this environment (`pip install "lm-eval==0.4.7"`).
5. **`tool_use` suite advertised but missing** from `LIST_OF_SUITES` (silent fallback to `affine_domain`).
6. **Frontier / domain leaderboard 100% cells** are **BASELINE_TABLE_ONLY** except Clang/rational/healthz/LLVM CLI measured rows.
7. **Mock LLM accuracy 0%** — expected; do not cite as model quality. Need real provider or Affine `/v1` chat for quality claims.
8. **Verify probe failure path** can report `status_code: 200` with `live: false` — honesty bug if network fails.
9. **Healthz RTT (120–280ms)** is network path; do not equate to claimed kernel latency `0.012s` in baseline tables.
10. **Wiki/docs claiming MMLU/GSM8k/HumanEval/MT-Bench 100%** need either real harness receipts or clear BASELINE_TABLE_ONLY labels (partially already noted in wiki FAQ/Benchmarks).
11. **Open-AGI hardest suites** — wrappers land in `bin/run-open-agi-harnesses.sh`; SWE-bench/LiveCodeBench remain NEEDS_UPSTREAM (exit 3); HLE/ARC/GAIA still need checkouts + gated data + JSON `/v1`.

---

## 6. Coordination facts for other agents

| Fact | Value |
|:---|:---|
| Workspace | `/Users/richardgillespie/Documents/AppleGaiaFTCL/llm-llvm-benchmark-suite` |
| Python | `/usr/bin/python3` 3.9.6 |
| Clang | `/usr/bin/clang` Apple clang 21.0.0 (arm64-darwin) |
| Pytest | 10/10 green |
| Dated receipt stamp | `20260720T222159Z` |
| Inventory doc | `docs/BENCHMARK_INVENTORY.md` (this file) |
| Wiki-ready copy | `wiki/Benchmark-Inventory.md` |
| Live health endpoint that works | `https://affine.earth/language-invariant/healthz` |
| `/v1` that works locally only | interceptor `python3 llm_llvm_bench/server/affine_v1_interceptor.py <port>` |
| Do not overwrite | Prefer `reports/receipts_<UTCSTAMP>/` for new measured runs |

---

*Generated by Workstream D inventory pass — measurements from stamp `20260720T222159Z` only. No invented harness scores.*
