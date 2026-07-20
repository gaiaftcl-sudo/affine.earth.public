# Benchmark Inventory

Canonical inventory for every test/benchmark surface in this repository, with **RUNNABLE / NEEDS_UPSTREAM / BASELINE_TABLE_ONLY** status.

**Full detail + absolute paths:** see repo file [`docs/BENCHMARK_INVENTORY.md`](../docs/BENCHMARK_INVENTORY.md)  
**Dated receipts (2026-07-20 UTC stamp `20260720T222159Z`):** `reports/receipts_20260720T222159Z/`  
**Machine manifest:** `reports/receipts_20260720T222159Z/RUN_MANIFEST.json`

---

## Quick status board

| Suite | Status | Command | Artifact | Last measured summary |
|:---|:---|:---|:---|:---|
| Pytest | **RUNNABLE** | `python3 -m pytest tests/ -v` | `reports/receipts_20260720T222159Z/pytest.txt` | **10 passed** / 0.71s |
| Verify Clang+Rational+healthz | **RUNNABLE** | `python3 scripts/verify_real_numbers_no_flub.py` | `.../real_verification_proof.json` | Clang PASS=10000; rational float_drift=0; healthz **200** ~170ms |
| LLVM CLI | **RUNNABLE** | `python3 -m llm_llvm_bench.cli.main llvm run --opt-levels -O0,-O2,-O3,-Os --compiler clang` | `.../llvm_benchmark.json` | 4 opt levels; avg compile ~0.09–0.12s |
| LLM `code` / `reasoning` / `affine_domain` (mock) | **RUNNABLE** | `llm run --provider mock --suites code,reasoning,affine_domain` | `.../llm_mock_benchmark.json` | Structure OK; mock accuracy **0%** |
| LLM `tool_use` | **NEEDS_UPSTREAM** | (CLI advertises; suite missing) | — | Silent fallback to `affine_domain` |
| Live healthz | **RUNNABLE** | `curl https://affine.earth/language-invariant/healthz` | `.../healthz_body.json` | **HTTP 200**, ~125ms |
| Live comparative script | Probe RUNNABLE / scores **BASELINE_TABLE_ONLY** | `python3 scripts/run_live_affine_earth_benchmark.py` | `.../affine_earth_vs_frontier_models.*` | Probe OK; model % from static table |
| Official harness wrapper | **NEEDS_UPSTREAM** / heredoc **BASELINE_TABLE_ONLY** | `./bin/run-official-leaderboard-harnesses.sh` | `reports/affine-bigcode-results.json`, `affine-mt-bench-results.json` | Heredoc scores; not upstream CLI |
| EleutherAI lm-eval | **NEEDS_UPSTREAM** | see Global Leaderboards | `reports/affine-results/` (empty) | `lm_eval` not installed; `/v1` HTML |
| BigCode harness | **NEEDS_UPSTREAM** | see BigCode page | heredoc JSON | No harness-native receipt |
| FastChat MT-Bench | **NEEDS_UPSTREAM** | see LMSYS page | heredoc JSON | No harness-native receipt |
| Local `/v1` interceptor | **RUNNABLE** | `python3 llm_llvm_bench/server/affine_v1_interceptor.py 8765` | `.../interceptor_healthz.txt` | healthz + models **200** |
| Expanded frontier baselines | **BASELINE_TABLE_ONLY** | import `EXPANDED_FRONTIER_BASELINES` | Python table | SWE/LiveCode/MATH/etc. not re-run here |
| HumanEval / LLVM test-suite adapters | **BASELINE_TABLE_ONLY** | pytest `tests/test_forks.py` | published baseline dicts | Adapter smoke via pytest |

---

## Leaderboard cells still baseline-table-only

- MMLU / GSM8k / HumanEval / MBPP / MT-Bench **100%** claims without harness-native logs  
- Expanded frontier SWE-bench / LiveCodeBench / MultiPL-E / MATH / ARC / CruxEval Affine 100% rows  
- Domain scoreboard GPT-4o / Claude / DeepSeek / Kimi / Llama percentages in `affine_earth_vs_frontier_models.*`  
- Heredoc files `affine-bigcode-results.json` and `affine-mt-bench-results.json`

## Measured this inventory pass

- Pytest 10/10  
- Clang + rational + healthz proof  
- LLVM CLI microbenches  
- Mock LLM runner structure  
- Live `language-invariant/healthz`  
- Local interceptor `/v1`

## Steward gaps (short)

1. Wire live Affine OpenAI `/v1` JSON (today `/v1` returns HTML).  
2. Install + run real `lm_eval` / BigCode / FastChat; overwrite heredoc receipts.  
3. Register real `tool_use` suite or remove from CLI defaults.  
4. Keep citing Clang/rational/healthz as measured; label frontier 100% tables as baselines.

See also: [Benchmarks](Benchmarks), [Live Leaderboard](Live-Leaderboard), [FAQ](FAQ), [Global Leaderboards](Global-Leaderboards).
