# Hardest Tests — Capability Map and Evidence Protocol

Large benchmark names are not capabilities by themselves. This page identifies
what each hard evaluation actually exercises, the upstream path to run it, and
the evidence required before any Affine.Earth result may be called **MEASURED**.

![Sovereign entry provenance: an evaluation identity begins with the public wallet flow](https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/signup-01-language-game-landing.png)

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
| [Humanity's Last Exam](https://lastexam.ai/) | Expert-level, multimodal and cross-domain questions designed to resist saturation | Evidence retrieval, long-horizon synthesis, answer-format fidelity, provenance | **RUNNABLE** with official release materials; no Affine score archived here |
| [ARC-AGI](https://arcprize.org/) | Few-example abstraction: infer a latent grid rule and transfer it to unseen inputs | Induction, compositional rule selection, exact output grids | **BASELINE_TABLE_ONLY** in existing comparison tables |
| [GPQA Diamond](https://arxiv.org/abs/2311.12022) | Graduate-level “Google-proof” questions written by domain experts | Scientific reasoning, calibrated uncertainty, distractor resistance | **RUNNABLE** through an upstream-compatible evaluator; no Affine result bundle archived |
| [FrontierMath](https://arxiv.org/abs/2411.04872) | Research-level mathematics requiring extended derivations | Formal derivation, exact rational checks, proof/citation separation | **RUNNABLE** only where benchmark access and evaluation terms permit; no Affine score archived |
| [SWE-bench Verified](https://www.swebench.com/) | Resolve real GitHub issues in real repositories, then pass hidden tests | Repository navigation, patch minimality, test execution, dependency control | **BASELINE_TABLE_ONLY**; full Verified logs are required for MEASURED |
| [LiveCodeBench](https://livecodebench.github.io/) | Time-split contest coding designed to reduce training-data contamination | Algorithm design, implementation correctness, time-aware evaluation | **BASELINE_TABLE_ONLY**; no run bundle archived |
| [GAIA](https://huggingface.co/gaia-benchmark) | Tool-using, multi-step real-world tasks with a final verifiable answer | Planning, browsing/tool orchestration, file reasoning, final-answer exactness | **RUNNABLE** when the target exposes the required tool interface; no Affine score archived |

## What “run it” means

### 1. Establish a live, identifiable target

Create a public evaluation identity through [Create Account / Signup](Create-Account-Signup), then preserve the model identifier and endpoint response. The current public `/v1` readiness boundary is explicit: healthz is observed live, while `/v1/models` must return JSON before an OpenAI-compatible harness run can be recorded.

```bash
export OPENAI_BASE_URL="https://your-compatible-host/v1"
export OPENAI_API_KEY="..."
curl --fail --show-error --silent \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  "$OPENAI_BASE_URL/models" | tee reports/provider_models.json
```

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
| HLE / GPQA / FrontierMath | Official task version, prompt policy, answer file, grader output, model/sampling manifest |
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
