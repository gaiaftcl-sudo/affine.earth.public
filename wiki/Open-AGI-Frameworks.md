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

| Suite | Harness key | Launcher state | Artifact destination |
|:---|:---|:---|:---|
| GPQA Diamond | `gpqa` | **RUNNABLE_WRAPPER** (`lm-eval==0.4.7`, `gpqa_diamond_cot_zeroshot`) | `reports/third_party/open_agi/gpqa/` |
| BIG-Bench Hard | `bbh` | **RUNNABLE_WRAPPER** (`bbh_cot_fewshot`) | `reports/third_party/open_agi/bbh/` |
| MMLU-Pro | `mmlu-pro` | **RUNNABLE_WRAPPER** (`mmlu_pro`) | `reports/third_party/open_agi/mmlu_pro/` |
| lm-eval hard bundle | `lm-eval-hard` | **RUNNABLE_WRAPPER** (GPQA + BBH + MMLU-Pro) | `reports/third_party/open_agi/lm_eval_hard/` |
| Humanity's Last Exam | `hle` | **RUNNABLE_WRAPPER** after gated dataset acceptance and `HF_TOKEN` | `reports/third_party/open_agi/hle/` |
| ARC-AGI | `arc-agi` | **RUNNABLE_WRAPPER** once checkout, task data, and model config are supplied | `reports/third_party/open_agi/arc_agi/` |
| ARC-AGI-2 | `arc-agi-2` | **RUNNABLE_WRAPPER**; refuses sample-task substitution | `reports/third_party/open_agi/arc_agi/` |
| GAIA | `gaia` | **RUNNABLE_WRAPPER** through Inspect AI (tool sandbox requirements apply) | `reports/third_party/open_agi/gaia/` |
| Inspect GPQA / generic | `inspect-gpqa` / `inspect` | **RUNNABLE_WRAPPER** (`INSPECT_TASK` for generic) | `reports/third_party/open_agi/inspect_*/` |
| LiveCodeBench | `livecodebench` | **RUNNABLE_WRAPPER** (checkout + real `lcb_runner`) | `reports/third_party/open_agi/livecodebench/` |
| SWE-bench Verified | `swe-bench` | **RUNNABLE_WRAPPER** when `SWE_BENCH_PREDICTIONS_PATH` points at real predictions JSONL | `reports/third_party/open_agi/swe_bench/` |
| FrontierMath | `frontiermath` | **NEEDS_UPSTREAM** — launcher exits **3** | no measured result directory |

```bash
# Configure a real JSON-capable target, then use a selected upstream wrapper.
cp configs/third-party-harnesses.env.example .env.third-party-harnesses
./bin/run-open-agi-harnesses.sh --harness lm-eval-hard
./bin/run-open-agi-harnesses.sh --harness hle
./bin/run-open-agi-harnesses.sh --harness arc-agi-2
./bin/run-open-agi-harnesses.sh --harness gaia
./bin/run-open-agi-harnesses.sh --harness livecodebench
export SWE_BENCH_PREDICTIONS_PATH=/path/to/predictions.jsonl
./bin/run-open-agi-harnesses.sh --harness swe-bench
./bin/run-open-agi-harnesses.sh --harness frontiermath   # exit 3
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
| HLE, GPQA/BBH/MMLU-Pro, ARC-AGI(-2), SWE-bench, LiveCodeBench, GAIA/Inspect | **RUNNABLE_WRAPPER** — see [Hardest Tests](Hardest-Tests); FrontierMath **NEEDS_UPSTREAM** (exit 3) |

## Citation rule

Use a status label in every caption or statement:

> **MEASURED:** command, model, UTC timestamp, benchmark revision, raw artifact
> path, and checksum.

> **BASELINE_TABLE_ONLY:** source table and publication reference, with no
> wording that implies the repository executed the benchmark.

This keeps the public narrative ambitious about the evaluation target and exact
about what has been demonstrated.

Next: [Hardest Tests](Hardest-Tests) · [Capabilities](Capabilities) · [Examples / Cookbook](Examples-Cookbook) · [FAQ](FAQ)

---

## Rig packaging, outsider commands, and research catalogue

Outsider-facing map of **hardest** public AGI / exam frameworks and how this
rig wires (or honestly refuses) them for Affine.Earth validation.

Companion packaging:

| File | Role |
|:---|:---|
| `configs/open-agi-harnesses.yaml` | suite IDs + harness keys + pins |
| `configs/third-party-harnesses.yaml` | cross-links into open-AGI keys |
| `bin/run-open-agi-harnesses.sh` | thin upstream launcher (no fake scores) |
| [Third-Party Harness Reproduction](Third-Party-Harness-Reproduction) | MMLU / GSM8K / HumanEval / MT-Bench |

**Rule:** a score is **MEASURED** only with upstream artifacts + exact command +
pin/revision + model id + base URL class. This repo never writes heredoc
scores for these frameworks.

## Status table

| Suite ID | Harness key | Status | Upstream |
|:---|:---|:---|:---|
| `open_agi_hle` | `hle` | **RUNNABLE_WRAPPER** | [centerforaisafety/hle](https://github.com/centerforaisafety/hle) · dataset [cais/hle](https://huggingface.co/datasets/cais/hle) |
| `open_agi_arc_agi` | `arc-agi` | **RUNNABLE_WRAPPER** | [arcprize/arc-agi-benchmarking](https://github.com/arcprize/arc-agi-benchmarking) |
| `open_agi_arc_agi_2` | `arc-agi-2` | **RUNNABLE_WRAPPER** | [ARC-AGI-2](https://github.com/arcprize/ARC-AGI-2) data + ARC Prize CLI (no sample substitution) |
| `open_agi_gpqa` | `gpqa` | **RUNNABLE_WRAPPER** | lm-eval `gpqa_diamond_cot_zeroshot` |
| `open_agi_bbh` | `bbh` | **RUNNABLE_WRAPPER** | lm-eval `bbh_cot_fewshot` |
| `open_agi_mmlu_pro` | `mmlu-pro` | **RUNNABLE_WRAPPER** | lm-eval `mmlu_pro` |
| `open_agi_lm_eval_hard` | `lm-eval-hard` | **RUNNABLE_WRAPPER** | lm-eval GPQA+BBH+MMLU-Pro bundle |
| `open_agi_gaia` | `gaia` | **RUNNABLE_WRAPPER** | Inspect `inspect_evals/gaia` |
| `open_agi_inspect_gpqa` | `inspect-gpqa` | **RUNNABLE_WRAPPER** | Inspect `inspect_evals/gpqa_diamond` |
| `open_agi_inspect` | `inspect` | **RUNNABLE_WRAPPER** | Inspect via `INSPECT_TASK` |
| `open_agi_livecodebench` | `livecodebench` | **RUNNABLE_WRAPPER** | [LiveCodeBench](https://github.com/LiveCodeBench/LiveCodeBench) `lcb_runner.runner.main` |
| `open_agi_swe_bench` | `swe-bench` | **RUNNABLE_WRAPPER** | [SWE-bench](https://github.com/SWE-bench/SWE-bench) scorer needs real predictions JSONL |
| `open_agi_frontiermath` | `frontiermath` | **NEEDS_UPSTREAM** | [Epoch FrontierMath](https://epoch.ai/frontiermath) — wrapper exits 3 |

## Gate 0 — endpoint reality

Same as third-party harnesses: `https://affine.earth/v1` currently returns an
HTML SPA, not OpenAI JSON. Point harnesses at a real OpenAI-compatible `/v1`
that answers `GET …/models` with JSON. Local interceptor is wiring only, not a
public AGI score claim.

```bash
cp configs/third-party-harnesses.env.example .env.third-party-harnesses
# set AFFINE_HARNESS_ENDPOINT, AFFINE_HARNESS_MODEL, OPENAI_API_KEY / AFFINE_HARNESS_API_KEY
# HLE uses https://huggingface.co/datasets/cais/hle; follow its non-redistribution notice.
```

## Outsider commands

### lm-eval hard tasks (GPQA / BBH / MMLU-Pro)

```bash
python -m pip install "lm-eval==0.4.7"
./bin/run-open-agi-harnesses.sh --harness gpqa          # gpqa_diamond_cot_zeroshot
./bin/run-open-agi-harnesses.sh --harness bbh           # bbh_cot_fewshot
./bin/run-open-agi-harnesses.sh --harness mmlu-pro
./bin/run-open-agi-harnesses.sh --harness lm-eval-hard  # all three
```

Artifacts under `reports/third_party/open_agi/{gpqa,bbh,mmlu_pro,lm_eval_hard}/`.

### Humanity's Last Exam (HLE)

```bash
git clone --depth 1 https://github.com/centerforaisafety/hle.git harnesses/hle
python -m pip install -r harnesses/hle/requirements.txt
# optional smoke: export HLE_MAX_SAMPLES=3
./bin/run-open-agi-harnesses.sh --harness hle
# judge: export HLE_RUN_JUDGE=1
```

Dataset: Hugging Face `cais/hle` (accept terms). Site: https://lastexam.ai/

If the checkout or `HF_TOKEN` is missing, the launcher exits non-zero and does
**not** invent an accuracy percentage.

### ARC-AGI / ARC-AGI-2

```bash
git clone --depth 1 https://github.com/arcprize/arc-agi-benchmarking.git \
  harnesses/arc-agi-benchmarking
(cd harnesses/arc-agi-benchmarking && uv sync)
export ARC_AGI_CONFIG="your-models-yml-config-name"

# ARC-AGI-1 or custom task folder:
export ARC_AGI_DATA_DIR="/absolute/path/to/tasks"
./bin/run-open-agi-harnesses.sh --harness arc-agi

# ARC-AGI-2 public evaluation (refuses sample-task substitution):
git clone --depth 1 https://github.com/arcprize/ARC-AGI-2.git harnesses/ARC-AGI-2
./bin/run-open-agi-harnesses.sh --harness arc-agi-2
```

Score with upstream `scoring.py` inside the ARC Prize checkout. Submissions
land under `reports/third_party/open_agi/arc_agi/submissions/` by default.

ARC-AGI-3 interactive environments ([arc-agi-3-benchmarking](https://github.com/arcprize/arc-agi-3-benchmarking),
`ARC_API_KEY`) are a separate track — not wrapped here yet.

### Inspect AI (GAIA / GPQA / generic)

```bash
python -m pip install "inspect-ai" "inspect-evals"
./bin/run-open-agi-harnesses.sh --harness gaia           # Docker typically required
./bin/run-open-agi-harnesses.sh --harness inspect-gpqa
export INSPECT_TASK=inspect_evals/gaia_level1
./bin/run-open-agi-harnesses.sh --harness inspect
```

Logs under `reports/third_party/open_agi/{gaia,inspect_gpqa,inspect}/`.

### LiveCodeBench (real CLI)

```bash
git clone --depth 1 https://github.com/LiveCodeBench/LiveCodeBench.git \
  harnesses/LiveCodeBench
python -m pip install -e harnesses/LiveCodeBench
./bin/run-open-agi-harnesses.sh --harness livecodebench
```

Fails loudly if checkout/`lcb_runner` is missing. Does not invent Pass@k.

### SWE-bench Verified (official scorer; real predictions required)

```bash
python -m pip install swebench   # or editable checkout under harnesses/SWE-bench
# Agent must already have written predictions JSONL:
#   {instance_id, model_name_or_path, model_patch}
export SWE_BENCH_PREDICTIONS_PATH="/absolute/path/predictions.jsonl"
# or: export SWE_BENCH_PREDICTIONS_PATH=gold   # harness self-check only
./bin/run-open-agi-harnesses.sh --harness swe-bench
```

Exits 2 if predictions are missing. Never fabricates patches or resolved-%.

### FrontierMath (honest NEEDS_UPSTREAM)

```bash
./bin/run-open-agi-harnesses.sh --harness frontiermath   # exit 3
```

No public full suite. Epoch access / evaluation terms govern any MEASURED claim.

## Provenance checklist

For any MEASURED open-AGI claim, retain:

1. Upstream artifact directory under `reports/third_party/open_agi/`
2. Exact command line + env keys (no secrets)
3. Pin/revision from `configs/open-agi-harnesses.yaml`
4. Model id + base URL class
5. Dataset access note (e.g. HF gated acceptance timestamp)

See also [Un-Mocked Methodology](Un-Mocked-Verification-Methodology-and-Instructions) and
[Benchmark Inventory](Benchmark-Inventory).

Related wiki pages:

- [Open AGI Frameworks](Open-AGI-Frameworks)
- [Hardest Tests](Hardest-Tests)
- [Third-Party Harness Reproduction](Third-Party-Harness-Reproduction)

## Research catalogue: benchmark access, difficulty, and API fit

This catalogue distinguishes a public reproduction path from a private
leaderboard or held-out evaluation. It documents no Affine result.

### Humanity's Last Exam (HLE)

- **Official:** [website](https://lastexam.ai/),
  [evaluator](https://github.com/centerforaisafety/hle),
  [dataset](https://huggingface.co/datasets/cais/hle), and
  [paper](https://arxiv.org/abs/2501.14249).
- **Measures / difficulty:** 2,500 multimodal, closed-ended expert academic
  questions across more than 100 subjects. It reports accuracy and calibration
  and is designed as a frontier-knowledge benchmark.
- **Runnable:** yes; the official repository contains `hle_eval`. The data card
  carries MIT metadata and asks users not to redistribute prompts, images, or
  answers. A private held-out component exists, so a public-data run cannot
  establish a private-test score.
- **API:** the simple evaluator uses the Python OpenAI client. It needs a
  compatible Affine base URL or a client adapter. Record the judge model, since
  it grades short answers.

  ```bash
  git clone https://github.com/centerforaisafety/hle.git
  cd hle/hle_eval
  python -m pip install -r requirements.txt
  python run_model_predictions.py --dataset cais/hle --model "$AFFINE_MODEL" \
    --max_completion_tokens 8192 --num_workers 4 --max_samples 3
  python run_judge_results.py --dataset cais/hle \
    --predictions "hle_${AFFINE_MODEL}.json" --num_workers 4
  ```

### ARC-AGI / ARC-AGI-2

- **Official:** [ARC-AGI-1](https://github.com/fchollet/ARC-AGI),
  [ARC-AGI-2](https://github.com/arcprize/ARC-AGI-2), and the
  [ARC Prize guide](https://arcprize.org/guide/1).
- **Measures / difficulty:** induction of a novel grid-transformation rule
  from a handful of examples. ARC-AGI-2 has 1,000 public training tasks and
  120 public evaluation tasks; its repository reports 66% human performance in
  its test sample.
- **Runnable:** public JSON tasks are directly runnable, but the data
  repository is not a drop-in OpenAI-chat harness. It includes private
  competition sets that cannot be reproduced locally.
- **License / caveats:** Apache-2.0. Repeated prompt/agent tuning on the public
  evaluation set destroys its use as an unseen test.
- **API:** write an adapter that sends a text/grid representation to the
  Affine endpoint, parses a valid task-output JSON, and runs a pinned public
  scorer. Prompt representation, allowed attempts, and output repair are
  evaluation conditions.

  ```bash
  git clone https://github.com/arcprize/ARC-AGI-2.git
  # Public evaluation tasks: ARC-AGI-2/data/evaluation/*.json
  ```

### GPQA Diamond

- **Official:** [repository](https://github.com/idavidrein/gpqa),
  [dataset](https://huggingface.co/datasets/Idavidrein/gpqa),
  [lm-eval task](https://github.com/EleutherAI/lm-evaluation-harness/tree/main/lm_eval/tasks/gpqa),
  and [Inspect task](https://github.com/UKGovernmentBEIS/inspect_evals/tree/main/src/inspect_evals/gpqa).
- **Measures / difficulty:** graduate biology, physics, and chemistry
  multiple-choice reasoning. The authors report 65% domain-PhD-expert
  accuracy and 34% skilled non-expert accuracy with web access.
- **Runnable:** yes through lm-eval, Inspect Evals, or OpenAI `simple-evals`
  after accepting the gated Hugging Face terms.
- **License / caveats:** CC-BY-4.0 dataset metadata plus gated access terms.
  Report variant, prompting, repeats, and any browsing/tool access.
- **API:** native through lm-eval's `local-chat-completions` and Inspect's
  `openai-api` provider.

  ```bash
  python -m pip install "lm_eval[api]"
  lm_eval --model local-chat-completions \
    --model_args "model=$AFFINE_MODEL,base_url=$AFFINE_OPENAI_BASE_URL/chat/completions" \
    --tasks gpqa_diamond_cot_zeroshot --batch_size 1 --log_samples \
    --output_path reports/third_party/gpqa
  ```

### FrontierMath

- **Official:** [FrontierMath](https://epoch.ai/frontiermath) and
  [tiers 1–4](https://epoch.ai/frontiermath/tiers-1-4/the-benchmark).
- **Measures / difficulty:** original advanced mathematics problems, from
  undergraduate material through research-level Tier 4; relevant experts may
  require hours or days.
- **Runnable:** **not as a full public suite**. Epoch publishes representative
  samples, keeps the core data private to limit contamination, and directs
  evaluation access requests to `math_evals@epoch.ai`.
- **License / caveats / API:** no public universal runner or reproducible full
  dataset. Do not claim a full FrontierMath result from public samples.

### LiveCodeBench

- **Official:** [repository](https://github.com/LiveCodeBench/LiveCodeBench)
  and [site](https://livecodebench.github.io/).
- **Measures / difficulty:** contamination-aware coding from recent contest
  problems, including code generation and execution. The official scorer
  computes executable-test `pass@1` / `pass@5`.
- **Runnable:** yes. Pin a named data release and date window. Generated code
  must execute inside a suitable sandbox.
- **License / caveats:** MIT. The upstream provider integration supports major
  APIs; a custom Affine endpoint may need a provider-model entry.
- **API command:**

  ```bash
  git clone https://github.com/LiveCodeBench/LiveCodeBench.git
  cd LiveCodeBench && python -m pip install -e .
  python -m lcb_runner.runner.main --model "$AFFINE_MODEL" \
    --scenario codegeneration --evaluate --release_version release_v6
  ```

### SWE-bench Verified

- **Official:** [repository/evaluator](https://github.com/SWE-bench/SWE-bench),
  [Verified data](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified),
  and [release description](https://openai.com/index/introducing-swe-bench-verified/).
- **Measures / difficulty:** an agent must repair an actual repository issue
  with a patch that passes the instance's test suite. Verified comprises 500
  human-validated solvable tasks.
- **Runnable:** yes via the official Docker harness or Modal. It consumes
  prediction JSONL, so an Affine coding agent must create patches before the
  scorer is run.
- **License / caveats:** MIT. Agent tooling, timeouts, container images, and
  dataset revision are part of the method. Test the evaluator with gold patches
  before measuring a model.
- **API command:** the scorer does not call a chat API itself:

  ```bash
  python -m swebench.harness.run_evaluation \
    --dataset_name SWE-bench/SWE-bench_Verified \
    --predictions_path ./affine_predictions.jsonl \
    --max_workers 8 --run_id affine-verified
  ```

### GAIA, AgentBench, and BrowseComp

| Benchmark | Official sources | Measures / public access | License and API integration |
|:---|:---|:---|:---|
| **GAIA** | [dataset](https://huggingface.co/datasets/gaia-benchmark/GAIA), [Inspect implementation](https://github.com/UKGovernmentBEIS/inspect_evals/tree/main/src/inspect_evals/gaia) | 466 realistic assistant tasks spanning browsing, files, code, multimodality, and reasoning. Gated public validation plus private-test answers. Inspect uses Docker tools. | Dataset terms prohibit reshare; model endpoint works through Inspect `openai-api`. `pip install "inspect-evals[gaia]"`; also needs `HF_TOKEN` and Docker. |
| **AgentBench** | [repository](https://github.com/THUDM/AgentBench), [paper](https://arxiv.org/abs/2308.03688) | Multi-turn agents in eight environments; public dev split, private test/extend splits. | Apache-2.0. OpenAI-style YAML agent configuration; custom compatible endpoint needs the API-agent config adapted. |
| **BrowseComp** | [announcement](https://openai.com/index/browsecomp), [reference](https://github.com/openai/simple-evals), [paper](https://arxiv.org/abs/2504.12516) | 1,266 persistent web-research questions with short verifiable answers. Public reference code, but requires a browsing agent rather than answer-only chat. | `simple-evals` is MIT. Do not republish examples; retain browser/search stack and web date. Reference is OpenAI-oriented, so custom base URL integration requires an adapter. |

### BIG-Bench Hard and MMLU-Pro

| Benchmark | Official sources | Measures / runnable state | License and API integration |
|:---|:---|:---|:---|
| **BIG-Bench Hard** | [repository](https://github.com/suzgunmirac/BIG-Bench-Hard), [lm-eval task](https://github.com/EleutherAI/lm-evaluation-harness/tree/main/lm_eval/tasks/bbh) | 23 multi-step reasoning tasks chosen because early LLMs did not beat average human raters. Direct or lm-eval runnable. | MIT. Older public regression suite, not contamination-resistant frontier evidence. lm-eval's OpenAI-compatible adapters work. |
| **MMLU-Pro** | [repository](https://github.com/TIGER-AI-Lab/MMLU-Pro), [dataset](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro), [lm-eval task](https://github.com/EleutherAI/lm-evaluation-harness/tree/main/lm_eval/tasks/mmlu_pro) | Harder, 10-choice broad knowledge/reasoning benchmark. Official scripts and lm-eval run today. | Apache-2.0. Official `evaluate_from_apiX.py` supports a universal OpenAI `chat.completions` base URL; report the prompt/few-shot regime. |

## Framework choices beyond individual datasets

### Inspect AI + Inspect Evals — primary framework

- **Official:** [Inspect](https://inspect.aisi.org.uk/),
  [source](https://github.com/UKGovernmentBEIS/inspect_ai), and
  [Inspect Evals](https://github.com/UKGovernmentBEIS/inspect_evals).
- **License:** MIT for both framework and task package; datasets retain their
  own licenses.
- **Fit:** native `openai-api` model provider, tools, agent bridges, Docker
  sandboxes, structured logs, and a viewer. It is the strongest first
  integration target for an Affine JSON API.

  ```bash
  python -m pip install inspect-ai inspect-evals
  inspect eval inspect_evals/gpqa_diamond \
    --model "openai-api/$AFFINE_MODEL" \
    --model-base-url "$AFFINE_OPENAI_BASE_URL"
  ```

### EleutherAI lm-evaluation-harness

- **Official:** [source](https://github.com/EleutherAI/lm-evaluation-harness)
  and [API guide](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/API_guide.md).
- **License:** MIT; individual task data varies.
- **Fit:** broad task catalog and native `local-completions` /
  `local-chat-completions` adapters. This repository currently uses
  `lm-eval==0.4.7`; lock any upgrade plus task revision before comparison.

  ```bash
  python -m pip install "lm_eval[api]"
  lm_eval --model local-chat-completions \
    --model_args "model=$AFFINE_MODEL,base_url=$AFFINE_OPENAI_BASE_URL/chat/completions" \
    --tasks gpqa_diamond_cot_zeroshot,mmlu_pro,bbh_cot_fewshot \
    --batch_size 1 --log_samples --output_path reports/third_party/lm-eval-frontier
  ```

### HELM, OpenCompass, and OpenAI Evals

| Framework | Official URL / license | API fit and install |
|:---|:---|:---|
| **HELM** | [Stanford CRFM HELM](https://github.com/stanford-crfm/helm), Apache-2.0 | `pip install crfm-helm`. Broad, holistic scenarios and web UI. A private/custom endpoint is configured through local `prod_env/` deployment YAML; heavier integration than Inspect. |
| **OpenCompass** | [OpenCompass](https://github.com/open-compass/OpenCompass), Apache-2.0 | `pip install "opencompass[api]"`. Its `OpenAI` model config accepts `openai_api_base`, making it suitable for a compatible Affine endpoint. |
| **OpenAI Evals** | [openai/evals](https://github.com/openai/evals), MIT | `pip install evals` for the legacy local framework. The hosted [Evals API](https://developers.openai.com/api/docs/guides/evals) is OpenAI-platform-specific, not a generic endpoint runner. Use the source chiefly for reference implementations such as BrowseComp. |
