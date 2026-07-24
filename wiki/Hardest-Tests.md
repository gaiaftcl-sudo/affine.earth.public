# Hardest Tests — Capability Map and Evidence Protocol

![Sovereign entry — evaluation identity starts at the public wallet gate](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/hardest-tests-identity-gate.png)

![MEASURED vs BASELINE evidence labels](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/banner-measured-vs-baseline.png)

Large benchmark names are not capabilities by themselves. This page identifies
what each hard evaluation actually exercises, the upstream path to run it, and
the evidence required before any Affine.Earth result may be called **MEASURED**.

Story spine: [Home](Home) → [In action](In-Action) (UI all-tests) → [Results & Scores](Results-And-Scores) → [AGI agent execution](AGI-Agent-Execution).  
Identity once: [Create account](Create-Account-Signup) (signup video **only** there).

### Live product gallery

| Caption | Image |
|:---|:---|
| Games catalog (UI FoT) | ![games](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/ui-tests-07-games-catalog.png) |
| Linguistic membrane answer | ![lm](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/ui-tests-10-linguistic_membrane-answer.png) |
| Live healthz JSON | ![healthz](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/healthz-json-live.png) |

## UI FoT before hard-suite claims

Before treating any hard suite as **MEASURED** against Affine, exercise the in-product Games battery. Full video + chapter stills: **[In action](In-Action)**. That is **UI FoT**, not HumanEval / HLE / SWE-bench Pass@k.

## Read the status label first

| Label | Meaning |
|:---|:---|
| **MEASURED** | A dated run has command, target model, upstream revision, raw log, metric output, and checksums. |
| **RUNNABLE** | The documented command can be prepared and executed, but this wiki does not yet carry a complete result bundle. |
| **BASELINE_TABLE_ONLY** | A comparison table or published aggregate exists; it is not a run performed and archived by this project. |

The currently measured Affine suite surfaces are local pytest, exact-rational +
Clang receipts, LLVM microbenchmarks, and a live health observation. The
frontier suites below are a validation program, not a claim of completed pass
rates. See [Benchmark Inventory](Benchmark-Inventory).

## The hard-suite matrix

| Suite | What it demands | Affine validation focus | Current status |
|:---|:---|:---|:---|
| [Humanity's Last Exam](https://lastexam.ai/) | Expert-level, multimodal and cross-domain questions designed to resist saturation | Evidence retrieval, long-horizon synthesis, answer-format fidelity, provenance | **RUNNABLE** via `--harness hle`; no Affine score archived here |
| [ARC-AGI](https://arcprize.org/) / [ARC-AGI-2](https://github.com/arcprize/ARC-AGI-2) | Few-example abstraction: infer a latent grid rule and transfer it to unseen inputs | Induction, compositional rule selection, exact output grids | **RUNNABLE** via `--harness arc-agi` / `arc-agi-2` (no sample-task substitution); no Affine score archived |
| [GPQA Diamond](https://arxiv.org/abs/2311.12022) | Graduate-level “Google-proof” questions written by domain experts | Scientific reasoning, calibrated uncertainty, distractor resistance | **RUNNABLE** via `--harness gpqa` or `inspect-gpqa`; no Affine result bundle archived |
| [BIG-Bench Hard](https://github.com/suzgunmirac/BIG-Bench-Hard) / [MMLU-Pro](https://github.com/TIGER-AI-Lab/MMLU-Pro) | Multi-step reasoning and harder 10-choice knowledge suites | Chain-of-thought fidelity, broad-domain regression under lm-eval | **RUNNABLE** via `--harness bbh`, `mmlu-pro`, or `lm-eval-hard`; no Affine score archived |
| [FrontierMath](https://arxiv.org/abs/2411.04872) | Research-level mathematics requiring extended derivations | Formal derivation, exact rational checks, proof/citation separation | **NEEDS_UPSTREAM** — `--harness frontiermath` exits 3; no public full suite |
| [SWE-bench Verified](https://www.swebench.com/) | Resolve real GitHub issues in real repositories, then pass hidden tests | Repository navigation, patch minimality, test execution, dependency control | **RUNNABLE** scorer via `--harness swe-bench` when `SWE_BENCH_PREDICTIONS_PATH` is set; no Affine score archived |
| [LiveCodeBench](https://livecodebench.github.io/) | Time-split contest coding designed to reduce training-data contamination | Algorithm design, implementation correctness, time-aware evaluation | **RUNNABLE** via `--harness livecodebench` (`lcb_runner`); no run bundle archived |
| [GAIA](https://huggingface.co/gaia-benchmark) | Tool-using, multi-step real-world tasks with a final verifiable answer | Planning, browsing/tool orchestration, file reasoning, final-answer exactness | **RUNNABLE** via `--harness gaia` / `inspect` when the target exposes the required tool interface; no Affine score archived |

## Packaged launcher keys

Use `bin/run-open-agi-harnesses.sh` with the keys below. A launcher completion is
**not** a MEASURED score — retain upstream artifacts under
`reports/third_party/open_agi/`.

```bash
cp configs/third-party-harnesses.env.example .env.third-party-harnesses
# Edit AFFINE_HARNESS_ENDPOINT + AFFINE_HARNESS_MODEL (+ HF_TOKEN / checkouts).

./bin/run-open-agi-harnesses.sh --harness lm-eval-hard  # GPQA + BBH + MMLU-Pro
./bin/run-open-agi-harnesses.sh --harness hle
./bin/run-open-agi-harnesses.sh --harness arc-agi-2     # refuses sample substitution
./bin/run-open-agi-harnesses.sh --harness gaia
./bin/run-open-agi-harnesses.sh --harness inspect-gpqa
./bin/run-open-agi-harnesses.sh --harness livecodebench # real lcb_runner
export SWE_BENCH_PREDICTIONS_PATH=/path/to/predictions.jsonl
./bin/run-open-agi-harnesses.sh --harness swe-bench
./bin/run-open-agi-harnesses.sh --harness frontiermath  # exit 3 — NEEDS_UPSTREAM
```

Full outsider commands: [AGI agent execution](AGI-Agent-Execution) ·
[Upstream frameworks](Upstream-Frameworks).

## What “run it” means

### 1. Establish a live, identifiable target

Create a public evaluation identity through [Create Account / Signup](Create-Account-Signup), then preserve the model identifier and endpoint response. The current public `/v1` readiness boundary is explicit: healthz is observed live, while `/v1/models` must return JSON before an OpenAI-compatible harness run can be recorded.

```bash
# Measured 2026-07-24 — Affine.Earth OS membrane
export OPENAI_BASE_URL="https://affine.earth/v1"
export AFFINE_API_KEY="uum8d-hle-verifier"
export OPENAI_API_KEY="$AFFINE_API_KEY"  # wire → Affine.Earth OS
export MODEL_ID="franklin-membrane"
curl --fail --show-error --silent \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Accept: application/json" \
  "$OPENAI_BASE_URL/models" | tee reports/provider_models.json
```

Live model ids (same probe): `gaiaftcl-os`, `affine-earth-os-mcp`,
`franklin-membrane`, `franklin-membrane-exam`. Prefer
`developer-suite/examples/03_openai_models_and_chat.py` / `docs/OPENAI_V1.md`.

### 2. Pin the benchmark and capture the whole run

For each suite, record:

1. benchmark/upstream Git commit and package lockfile;
2. exact command, model ID, sampling parameters, and UTC start/end;
3. raw model answers or patches where the benchmark permits retention;
4. upstream metric JSON, stdout/stderr, and SHA-256 checksums;
5. host and runtime details sufficient to reproduce the execution environment.

For repository-repair suites, retain the generated patch and the test result for
each instance. For question-answering suites, retain the answer record and
grader configuration. A score without this bundle remains a table entry.

### 3. Archive under a dated evidence directory

```bash
mkdir -p reports/third_party/<suite>/<utc-run-id>
# place upstream logs, metrics, model manifest, and command record here
find reports/third_party/<suite>/<utc-run-id> -type f -print0 | sort -z \
  | xargs -0 shasum -a 256 > reports/third_party/<suite>/<utc-run-id>/SHA256SUMS.txt
```

## Why these tests complement the Affine rig

The local rig gives a reproducible floor: Python tests, exact rational
arithmetic, real Clang compilation/execution, LLVM optimization telemetry, and
a live service liveness probe. The hard suites test a different ceiling:

- **HLE / GPQA Diamond / FrontierMath** stress expert reasoning and verification.
- **ARC-AGI** asks whether the system can infer a new abstraction from very few
  demonstrations rather than pattern-match a familiar task.
- **SWE-bench Verified / LiveCodeBench** test whether reasoning survives
  implementation, tool use, repositories, and executable checks.
- **GAIA** tests whether a system can coordinate multiple external operations
  and return the exact final answer.

Together they form an AGI-framework validation narrative: evaluate reasoning,
abstraction, coding, tool use, and deterministic execution—then preserve
artifacts so another party can distinguish a result from a baseline.

## Suite-specific acceptance criteria

| Family | A credible measured result includes |
|:---|:---|
| HLE / GPQA / BBH / MMLU-Pro | Official task version, prompt policy, answer file, grader output, model/sampling manifest |
| FrontierMath | Official Epoch evaluation path only; launcher exits 3 (`NEEDS_UPSTREAM`) — samples are not a full-suite score |
| ARC-AGI | Dataset split/version, exact predicted grids, scorer output, no hidden-test exposure |
| SWE-bench | Instance list, container/environment provenance, generated patches, evaluator logs, resolved count |
| LiveCodeBench | Release/date cutoff, task IDs, submissions, execution logs, scorer output |
| GAIA | Dataset split, tool policy, tool traces where allowed, final-answer evaluator output |

## Current evidence boundary

Do not convert an entry in `expanded_frontier_baselines.py`, a dashboard value,
or a local interceptor response into a hard-suite result. Those are useful
planning surfaces, not independent evaluation evidence. The first complete
artifact bundle published for a suite changes that specific suite from
**BASELINE_TABLE_ONLY** or **RUNNABLE** to **MEASURED**.

Continue with [Open AGI Frameworks](Open-AGI-Frameworks), [Examples / Cookbook](Examples-Cookbook), [Third-Party Harness Reproduction](Third-Party-Harness-Reproduction), or the [FAQ](FAQ).
