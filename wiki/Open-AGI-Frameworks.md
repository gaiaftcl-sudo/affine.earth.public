# Open AGI Frameworks — Validation Beyond a Scoreboard

Affine.Earth is evaluated as a system, not as a single number. An AGI-oriented
validation program must show whether a target can reason, induce abstractions,
build working software, use tools, and produce evidence that survives
independent inspection.

## The five validation planes

| Plane | Question | Representative evaluations | Evidence that matters |
|:---|:---|:---|:---|
| Knowledge and expert reasoning | Can it answer difficult, unfamiliar questions with disciplined evidence? | Humanity's Last Exam, GPQA Diamond, FrontierMath | Answer records, grader output, model/sampling manifest |
| Abstraction and transfer | Can it infer a rule from sparse examples and apply it to a new case? | ARC-AGI | Predicted grids, task IDs, official scorer output |
| Software construction | Can it turn reasoning into changes that compile and pass tests? | SWE-bench Verified, LiveCodeBench, BigCode | Patches, containers, test logs, metric JSON |
| Agency and tool use | Can it sequence external operations and return a verifiable result? | GAIA, controlled tool tasks | Tool trace, final answer, environment policy |
| Deterministic execution | Can the surrounding rig make claims auditable and repeatable? | pytest, LLVM, rational receipts | Source SHA, compiler/runtime identity, raw receipts |

The [Hardest Tests](Hardest-Tests) page maps each public benchmark to its
current evidence status and reproduction requirements.

## Packaged launcher status

The workspace now includes `configs/open-agi-harnesses.yaml` and
`bin/run-open-agi-harnesses.sh`, a thin launcher that preserves upstream
artifacts and refuses to synthesize score JSON. Its current coverage is:

| Suite | Launcher state | Artifact destination |
|:---|:---|:---|
| GPQA Diamond | **RUNNABLE_WRAPPER** through pinned `lm-eval` | `reports/third_party/open_agi/gpqa/` |
| Humanity's Last Exam | **RUNNABLE_WRAPPER** after gated dataset acceptance and `HF_TOKEN` | `reports/third_party/open_agi/hle/` |
| ARC-AGI | **RUNNABLE_WRAPPER** once the official checkout, task data, and model config are supplied | `reports/third_party/open_agi/arc_agi/` |
| GAIA | **RUNNABLE_WRAPPER** through Inspect AI (tool sandbox requirements apply) | `reports/third_party/open_agi/gaia/` |
| SWE-bench / LiveCodeBench | **NEEDS_UPSTREAM**; the launcher exits non-zero rather than producing a score | no result directory is created as a measurement |
| FrontierMath | **NEEDS_UPSTREAM_ACCESS**; benchmark access and its official evaluation terms govern execution | only a real official artifact may be labeled measured |

```bash
# Configure a real JSON-capable target, then use a selected upstream wrapper.
cp configs/third-party-harnesses.env.example .env.third-party-harnesses
./bin/run-open-agi-harnesses.sh --harness gpqa
```

The wrapper is an orchestration and provenance aid. The upstream evaluator
still supplies the metric; a launcher completion alone is not a score.

## What Affine contributes

The public harness already supplies a reproducible execution substrate:

- exact numerator/denominator arithmetic receipts;
- real Clang compile-and-run evidence across `-O0`, `-O2`, `-O3`, and `-Os`;
- Python test and report-generation checks;
- an OpenAI-compatible evaluation path for a target that actually exposes JSON;
- upstream harness documentation for EleutherAI lm-eval, BigCode, and FastChat;
- a public health observation and wallet-based Sovereign entry flow.

This does not establish a frontier benchmark result by itself. It establishes
the measurement discipline required to make one meaningful.

## Evidence-first framework

```text
identity → endpoint validation → pinned benchmark → recorded execution
        → upstream scoring → artifact bundle → independently repeatable claim
```

1. **Identity.** Start with [Create Account / Signup](Create-Account-Signup)
   when testing the public Affine surface.
2. **Endpoint validation.** Confirm `/models` and one real completion return
   the expected JSON before starting a compatible harness.
3. **Pinned benchmark.** Record task release, harness revision, dependencies,
   and permitted evaluation settings.
4. **Recorded execution.** Keep commands, output, generated answers/patches,
   and errors.
5. **Upstream scoring.** Prefer official graders and unmodified evaluator
   outputs.
6. **Artifact bundle.** Checksum all files and publish enough context for a
   third party to inspect the result.

## What the framework refuses to collapse

These distinctions are deliberately preserved:

- a liveness probe is not a model-evaluation result;
- a local API-shape interceptor is not a live Affine inference endpoint;
- a baseline comparison table is not a measured Affine pass rate;
- a passing unit test is not proof of broad reasoning capability;
- an impressive answer is not a benchmark score until the official grader
  produces an artifact.

## Framework progress board

| Capability plane | Public status |
|:---|:---|
| Deterministic local execution | **MEASURED** — pytest, rational/Clang, LLVM receipt paths |
| Service liveness and signup surface | **MEASURED** — healthz and public signup-surface checks |
| Live OpenAI-compatible inference | **PENDING** — must return actual `/v1` JSON before scoring |
| Upstream coding/reasoning harnesses | **RUNNABLE** — reproduction procedures documented |
| HLE, GPQA Diamond, FrontierMath, ARC-AGI, SWE-bench, LiveCodeBench, GAIA | **RUNNABLE** or **BASELINE_TABLE_ONLY** — see [Hardest Tests](Hardest-Tests) |

## Citation rule

Use a status label in every caption or statement:

> **MEASURED:** command, model, UTC timestamp, benchmark revision, raw artifact
> path, and checksum.

> **BASELINE_TABLE_ONLY:** source table and publication reference, with no
> wording that implies the repository executed the benchmark.

This keeps the public narrative ambitious about the evaluation target and exact
about what has been demonstrated.

Next: [Hardest Tests](Hardest-Tests) · [Capabilities](Capabilities) · [Examples / Cookbook](Examples-Cookbook) · [FAQ](FAQ)
