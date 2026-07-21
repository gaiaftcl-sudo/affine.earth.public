# AGI agent execution

How agents run open AGI / hard suites against a configured endpoint. This page is **commands + scoring posture**. For full third-party harness manuals, use [Upstream frameworks](Upstream-Frameworks).

Identity for live Affine UI work: [Create account (once)](Create-Account-Signup). Proof the product answers Games: [In action](In-Action).

---

## Preflight

```bash
git clone https://github.com/gaiaftcl-sudo/affine.earth.public.git
cd affine.earth.public
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,harnesses]"   # as needed for lm-eval / Inspect

cp configs/third-party-harnesses.env.example .env.third-party-harnesses
# Set AFFINE_HARNESS_ENDPOINT + AFFINE_HARNESS_MODEL to a JSON /v1 host.
# https://affine.earth/v1 may still return HTML SPA — do not leave that until /models is JSON.

curl --fail -sS -H "Authorization: Bearer $OPENAI_API_KEY" \
  "${AFFINE_HARNESS_ENDPOINT%/}/models" | tee reports/provider_models.json
```

Local green (no AGI Pass@k):

```bash
./bin/verify-rig.sh
```

---

## Run open AGI harnesses

Suite registry: [`configs/open-agi-harnesses.yaml`](https://github.com/gaiaftcl-sudo/affine.earth.public/blob/main/configs/open-agi-harnesses.yaml).  
Docs: [`docs/OPEN_AGI_FRAMEWORKS.md`](https://github.com/gaiaftcl-sudo/affine.earth.public/blob/main/docs/OPEN_AGI_FRAMEWORKS.md).

```bash
./bin/run-open-agi-harnesses.sh --harness lm-eval-hard  # GPQA + BBH + MMLU-Pro
./bin/run-open-agi-harnesses.sh --harness hle           # needs HF_TOKEN + gated cais/hle
./bin/run-open-agi-harnesses.sh --harness arc-agi-2     # refuses sample substitution
./bin/run-open-agi-harnesses.sh --harness gaia          # Inspect AI
./bin/run-open-agi-harnesses.sh --harness inspect-gpqa
./bin/run-open-agi-harnesses.sh --harness livecodebench # needs LiveCodeBench checkout
export SWE_BENCH_PREDICTIONS_PATH=/path/to/predictions.jsonl
./bin/run-open-agi-harnesses.sh --harness swe-bench
./bin/run-open-agi-harnesses.sh --harness frontiermath  # exit 3 — NEEDS_UPSTREAM
```

Artifacts land under `reports/third_party/open_agi/<suite>/`. A green launcher exit is **not** automatically a MEASURED wiki score — retain upstream output, then update [Results & Scores](Results-And-Scores).

---

## Status cheat sheet

| Key | State |
|:---|:---|
| `lm-eval-hard`, `gpqa`, `bbh`, `mmlu-pro` | RUNNABLE_WRAPPER (`lm-eval==0.4.7`) |
| `hle` | RUNNABLE_WRAPPER (HF gated) |
| `arc-agi`, `arc-agi-2` | RUNNABLE_WRAPPER |
| `gaia`, `inspect`, `inspect-gpqa` | RUNNABLE_WRAPPER (Inspect) |
| `livecodebench` | RUNNABLE_WRAPPER (`lcb_runner`) |
| `swe-bench` | RUNNABLE_WRAPPER (needs predictions JSONL) |
| `frontiermath` | NEEDS_UPSTREAM (exit 3) |

---

## Upstream (deep docs — we do not re-teach)

| Framework | Link |
|:---|:---|
| EleutherAI lm-evaluation-harness | https://github.com/EleutherAI/lm-evaluation-harness |
| Inspect AI | https://inspect.aisi.org.uk/ |
| Humanity's Last Exam | https://lastexam.ai/ · https://huggingface.co/datasets/cais/hle |
| ARC Prize / ARC-AGI-2 | https://arcprize.org/ · https://github.com/arcprize/ARC-AGI-2 |
| GAIA | https://huggingface.co/gaia-benchmark |
| SWE-bench | https://www.swebench.com/ |
| LiveCodeBench | https://livecodebench.github.io/ |
| BigCode harness | https://github.com/bigcode-project/bigcode-evaluation-harness |

Full link list: [Upstream frameworks](Upstream-Frameworks).
