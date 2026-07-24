# AGI agent execution

How agents run open AGI / hard suites against a configured endpoint. This page is **commands + scoring posture**. For full third-party harness manuals, use [Upstream frameworks](Upstream-Frameworks).

Identity for live Affine UI work: [Create account (once)](Create-Account-Signup). Proof the product answers Games: [In action](In-Action).

> **FoT:** AGI-2 MEASURED Kaggle publicScore **0.00** (COMPLETE) — [ARC Prize ARC-AGI-2 live record](ARC-Prize-AGI-2-Kaggle-Live)

---

## Preflight

```bash
git clone https://github.com/gaiaftcl-sudo/affine.earth.public.git
cd affine.earth.public
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,harnesses]"   # as needed for lm-eval / Inspect

cp configs/third-party-harnesses.env.example .env.third-party-harnesses
# Measured membrane (2026-07-24):
export OPENAI_BASE_URL="https://affine.earth/v1"
export AFFINE_API_KEY="uum8d-hle-verifier"
export OPENAI_API_KEY="$AFFINE_API_KEY"  # wire → Affine.Earth OS
export MODEL_ID="franklin-membrane"
export AFFINE_HARNESS_ENDPOINT="$OPENAI_BASE_URL"
export AFFINE_HARNESS_MODEL="$MODEL_ID"

curl --fail -sS -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Accept: application/json" \
  "${AFFINE_HARNESS_ENDPOINT%/}/models" | tee reports/provider_models.json
```

Local green (no AGI Pass@k):

```bash
./bin/verify-rig.sh
```

ARC UI examination is a separate local evidence gate:
[ARC UI Audit Orchestrator](ARC-UI-Audit-Orchestrator). It records
permission-bound VideoToolbox capture, Cursor injection, nine-cell reduction,
JSON extraction, and artifact validation. It must be GREEN before an ARC
Kaggle submission is considered. Keep `configs/NO_KAGGLE_SUBMIT.lock` in
place; a local audit never supplies `ALLOW_KAGGLE_SUBMIT=1`.

---

## Run open AGI harnesses

Suite registry: [`configs/open-agi-harnesses.yaml`](https://github.com/gaiaftcl-sudo/affine.earth.public/blob/main/configs/open-agi-harnesses.yaml).  
Docs: [`docs/OPEN_AGI_FRAMEWORKS.md`](https://github.com/gaiaftcl-sudo/affine.earth.public/blob/main/docs/OPEN_AGI_FRAMEWORKS.md).

```bash
./bin/run-open-agi-harnesses.sh --harness lm-eval-hard  # GPQA + BBH + MMLU-Pro
./bin/run-open-agi-harnesses.sh --harness hle           # needs HF_TOKEN + gated cais/hle; [record](Humanitys-Last-Exam-Live)
./bin/run-open-agi-harnesses.sh --harness arc-agi-2     # refuses sample substitution
./bin/run-arc-prize-kaggle.sh                           # Kaggle ARC-AGI-3; needs rules accept — [record](ARC-Prize-Kaggle-Live)
# ARC Prize 2026 ARC-AGI-2 — public package, network-disabled notebook:
python3 kaggle/arc-prize-2026-agi-2/arc_agi_2_kaggle.py \
  --input-root data/arc-prize-2026-agi-2 \
  --output kaggle/arc-prize-2026-agi-2/submission.json
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
| `hle` | MEASURED_STEWARD_GATE — [CAIS + loopback record](Humanitys-Last-Exam-Live); accept `cais/hle` terms + classic `HF_TOKEN` required |
| `arc-agi`, `arc-agi-2` | RUNNABLE_WRAPPER |
| ARC Prize Kaggle (`run-arc-prize-kaggle.sh`) | **MEASURED** — publicScore **0.12** COMPLETE ref 54875048 — [live record](ARC-Prize-Kaggle-Live) |
| ARC Prize Kaggle ARC-AGI-2 | MEASURED — publicScore **0.00** — [live record](ARC-Prize-AGI-2-Kaggle-Live) |
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
