# Affine.Earth Public Benchmark Wiki

![Affine.Earth language-game — live Sovereign entry](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/hero-language-game.png)

![MEASURED vs BASELINE — evidence labels, not invented scores](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/banner-measured-vs-baseline.png)

**Public repository:** [`gaiaftcl-sudo/affine.earth.public`](https://github.com/gaiaftcl-sudo/affine.earth.public)  
**This wiki:** [`gaiaftcl-sudo/affine.earth.public/wiki`](https://github.com/gaiaftcl-sudo/affine.earth.public/wiki)  
**Harness package:** `llm-llvm-benchmark-suite/`  
**Live health endpoint:** `https://affine.earth/language-invariant/healthz`  
**Last local verification sync:** `2026-07-20 22:14:57 UTC`

---

## Visual tour (live UI — all Games tests + answers)

### Demo — UI all-tests battery (primary)

Onboard → **all 12 LIVE Games** → Franklin live replies in `#messageList` (Socratic clarifying turns). Measured 2026-07-20 against `https://affine.earth`.

<p>
<video controls width="720" poster="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/ui-tests-07-games-catalog.png">
  <source src="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-ui-all-tests.mp4" type="video/mp4">
  <source src="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-ui-all-tests.webm" type="video/webm">
</video>
</p>

![Animated — UI all Games + live answers](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/demo-ui-all-tests.gif)

> **MP4 / WebM / GIF:** [affine-earth-demo-ui-all-tests.mp4](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-ui-all-tests.mp4) · [webm](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-ui-all-tests.webm) · [demo-ui-all-tests.gif](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/demo-ui-all-tests.gif) · mirrored at [`docs/media/`](https://github.com/gaiaftcl-sudo/affine.earth.public/tree/main/docs/media).  
> **FoT:** live UI answers are Socratic membrane turns — **not** CLI harness scores. Do **not** claim HumanEval 100% from this chat demo. Click paths: [Human-Verifiable Test Bank](Human-Verifiable-Test-Bank-and-Answers) · [Hardest Tests — UI section](Hardest-Tests).

| Chapter still | Surface |
|:---|:---|
| ![catalog](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/ui-tests-07-games-catalog.png) | Games catalog (12 LIVE) |
| ![lm](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/ui-tests-10-linguistic_membrane-answer.png) | Linguistic membrane — live reply + clarifying bar |
| ![fm](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/ui-tests-11-formal_manifold-answer.png) | Formal manifold → live Q&A |
| ![code](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/ui-tests-12-coding-answer.png) | Coding — UMC + MCP → live Q&A |
| ![wallet](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/ui-tests-19-wallet_qfot-profile.png) | Wallet · QFOT Profile (PROVEN 100/1) |

### Shorter clip — signup → app → one Q&A

<p>
<video controls width="720" poster="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/signup-flow-05-app-opened.png">
  <source src="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-signup-app-qa.mp4" type="video/mp4">
  <source src="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-signup-app-qa.webm" type="video/webm">
</video>
</p>

![Animated walkthrough — consent → location → Create wallet → app → Games / Q&A](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/demo-signup-app-qa.gif)


---
## What this project is

The **Affine.Earth Public Benchmark Testing Suite** (`llm-llvm-benchmark-suite`) is a Python package for evaluating:

1. **LLM providers** on coding, reasoning, and Affine-domain tasks (OpenAI-compatible APIs, Ollama, mock provider for offline wiring checks).
2. **LLVM / Clang** compilation and runtime performance across optimization levels (`-O0`, `-O2`, `-O3`, `-Os`).
3. **Upstream industry harnesses** (EleutherAI `lm-evaluation-harness`, BigCode `bigcode-evaluation-harness`, LMSYS FastChat MT-Bench) cloned under `harnesses/`.
4. **Live endpoint probes** against `affine.earth` plus un-flubbed local Clang + exact rational-arithmetic receipts.

It is a **benchmark and documentation** project. Numbers below that come from local machine execution are labeled **measured**. Comparative frontier-model tables are labeled **baseline tables** (from `llm_llvm_bench/forks/expanded_frontier_baselines.py` and published model-card aggregates). Receipt JSON files under `reports/` are labeled by **file provenance**.

---

## What you can do today

- **Create an Affine.Earth account** via Sovereign entry (wallet) — see [Create Account / Signup](Create-Account-Signup) (step 1 for outsiders / third-party testing).
- Run local package tests, exact-rational/Clang verification, and LLVM
  optimization sweeps.
- Point the LLM runner at an OpenAI-compatible or Anthropic endpoint and retain
  per-prompt JSON/Markdown results.
- Probe the public Affine.Earth health endpoint and archive the raw response.
- Serve the local dashboard and check its `/api/status` endpoint.
- Clone, install, and invoke EleutherAI lm-eval, BigCode, and FastChat directly
  while retaining upstream-native artifacts.

Start with [Capabilities](Capabilities) for command-level behavior,
[Examples / Cookbook](Examples-Cookbook) for end-to-end runs,
[Reports & Artifacts](Reports-And-Artifacts) for evidence interpretation, and
[Third-Party Harness Reproduction](Third-Party-Harness-Reproduction) for
independent upstream runs.

The current local interceptor and official-harness wrapper are explicitly
documented as development/report-shape paths, not independent third-party
evaluation evidence. See [FAQ](FAQ) for the complete provenance boundary.

---

## Capability first: the hardest public tests

Scores only become meaningful when readers can see **what a test exercises**:
expert reasoning, sparse-rule induction, repository repair, fresh coding, or
tool-mediated task completion. Start with:

- [**Hardest Tests**](Hardest-Tests) — Humanity's Last Exam, ARC-AGI, GPQA
  Diamond, FrontierMath, SWE-bench, LiveCodeBench, and GAIA; each marked
  **MEASURED**, **RUNNABLE**, or **BASELINE_TABLE_ONLY**.
- [**Open AGI Frameworks**](Open-AGI-Frameworks) — the evidence-first
  validation model across reasoning, abstraction, software construction, tool
  use, and deterministic execution.

### Gallery — identity gate and receipts

| Caption | Image |
|:---|:---|
| Sovereign entry (New wallet + consent) | ![Sovereign entry](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/sovereign-entry-new-wallet.png) |
| Optional domain capabilities | ![Optional domain](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/sovereign-entry-optional-domain.png) |
| Live healthz (pretty-printed from HTTP 200 JSON) | ![healthz](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/healthz-json-live.png) |
| Local Clang / pytest terminal receipt | ![terminal](https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/affine_benchmark_terminal.jpg) |

![Evidence labels](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/banner-measured-vs-baseline.png)

---

## Latest measured local snapshot (re-runnable)

These values were produced by running the suite on macOS with system `clang` and `pytest` on **2026-07-20**:

| Check | Result | How to reproduce |
|:---|:---|:---|
| Pytest unit/integration suite | **10 passed** in ~2.9s | `python3 -m pytest tests/ -v` |
| Rational arithmetic (10,000 adds) | **float_drift = 0.0**, num/den digit lengths 8455/8452, ~41.9ms | `python3 scripts/verify_real_numbers_no_flub.py` |
| Live healthz probe | **HTTP 200**, latency ~124–277ms (network-dependent) | `curl -sS https://affine.earth/language-invariant/healthz` |
| Clang verify microbench `-O0` | compile **97.12ms**, exec **71.31ms**, `.text` **16,384 B**, output `PASS=10000` | same verify script |
| Clang verify microbench `-O3` | compile **100.60ms**, exec **67.76ms**, `.text` **16,384 B**, output `PASS=10000` | same verify script |
| Full LLVM CLI suite (`llvm run`) | avg compile ~0.096–0.106s; total `.text` **32,768 B** per opt level (2 programs × 16,384) | `python3 -m llm_llvm_bench.cli.main llvm run --opt-levels -O0,-O2,-O3,-Os --compiler clang` |
| Provenance stamp | `proven_status: REAL_NUMBERS_VERIFIED_NO_FLUB` | `reports/real_verification_proof.json` |

Example healthz body (truncated; live fields may evolve):

```json
{
  "ok": true,
  "gguf_present": false,
  "jit": true,
  "socratic": true,
  "game_turn": true,
  "mcp": true,
  "mcp_endpoint": "POST /language-invariant/mcp"
}
```

---

## Architecture at a glance

```text
llm-llvm-benchmark-suite/
├── bin/                          # Full-suite shell wrappers
├── llm_llvm_bench/
│   ├── cli/                      # llm-llvm-bench Click CLI
│   ├── llm/                      # Suites, providers, evaluator, runner
│   ├── llvm/                     # Clang driver, microbenchmarks, runner
│   ├── forks/                    # HumanEval / LLVM adapters + frontier baselines
│   ├── server/                   # OpenAI-compatible /v1 interceptor
│   ├── web/                      # Local dashboard (port 8888)
│   └── core/                     # Types, metrics, JSON/MD reporters
├── harnesses/                    # Upstream clones (lm-eval, BigCode, FastChat)
├── tests/                        # Pytest suite (10 tests as of 2026-07-20)
├── scripts/                      # Live verify + wiki publisher
├── reports/                      # Measured receipts (JSON + Markdown)
└── docs/                         # Methodology + submission notes
```

---

## Wiki map (start here)

### Essentials
| Page | Contents |
|:---|:---|
| [Getting Started](Getting-Started) | Install, env vars, first commands, expected outputs |
| [Test Suites](Test-Suites) | Full inventory of pytest + LLM + LLVM + harness suites |
| [Benchmarks](Benchmarks) | What is measured, how to run, how to read reports |
| [Examples / Cookbook](Examples-Cookbook) | Many end-to-end command recipes |
| [Capabilities](Capabilities) | Runnable surfaces and evidence boundaries |
| [Reports & Artifacts](Reports-And-Artifacts) | JSON schemas, inspection, and audit bundles |
| [Third-Party Harness Reproduction](Third-Party-Harness-Reproduction) | Clone/install/run upstream engines directly |
| [Hardest Tests](Hardest-Tests) | What the most demanding public suites exercise and how to run them |
| [Open AGI Frameworks](Open-AGI-Frameworks) | Evidence-first AGI validation narrative |
| [FAQ / Q&A](FAQ) | Detailed questions and answers |

### Results & methodology
| Page | Contents |
|:---|:---|
| [Live Leaderboard](Live-Leaderboard) | Comparative scoreboard + provenance notes |
| [Un-Mocked Verification Methodology](Un-Mocked-Verification-Methodology-and-Instructions) | Reproduction protocol |
| [Human-Verifiable Test Bank](Human-Verifiable-Test-Bank-and-Answers) | Prompts and ground-truth answers |

### Upstream harness pages
| Page | Engine |
|:---|:---|
| [EleutherAI lm-evaluation-harness](EleutherAI-lm-evaluation-harness) | MMLU, GSM8k |
| [BigCode bigcode-evaluation-harness](BigCode-bigcode-evaluation-harness) | HumanEval, MBPP |
| [LMSYS FastChat MT-Bench](LMSYS-FastChat-MT-Bench) | Multi-turn judge |
| [LLVM Official Test-Suite](LLVM-Official-Test-Suite) | Clang opt-level receipts |
| [Expanded Frontier Coding Suite](Expanded-Frontier-Coding-Suite) | SWE-bench, LiveCodeBench, MultiPL-E baselines |
| [Expanded Frontier Reasoning Suite](Expanded-Frontier-Reasoning-Suite) | MATH/AIME, ARC-AGI, CruxEval baselines |

---

## Quickest path to green

```bash
git clone https://github.com/gaiaftcl-sudo/affine.earth.public.git
cd affine.earth.public/llm-llvm-benchmark-suite   # or: cd llm-llvm-benchmark-suite
pip install -e .
python3 -m pytest tests/ -v
python3 scripts/verify_real_numbers_no_flub.py
./bin/run-full-benchmark.sh
```

Then open [Getting Started](Getting-Started) and [Examples / Cookbook](Examples-Cookbook).
