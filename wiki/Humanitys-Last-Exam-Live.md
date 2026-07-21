# Humanity’s Last Exam — live harness record

Official sources: [agi.safe.ai](https://agi.safe.ai/), the [CAIS HLE evaluator](https://github.com/centerforaisafety/hle), and the gated [cais/hle dataset](https://huggingface.co/datasets/cais/hle).

## Recorded 2026-07-21

| Check | Observed result |
|:---|:---|
| CAIS evaluator | Cloned at `26dca2e253b405105b4c3d8c2f5af06f86f90c66`; isolated `hle_eval/.venv` installed from the upstream root `requirements.txt` |
| Affine loopback | `http://127.0.0.1:8080/v1/models` returned OpenAI JSON through a transparent loopback proxy to the live local model service |
| Model endpoint | A live `qwen/qwen3.6-35b-a3b` completion returned HTTP 200; the deliberately short 16-token probe exhausted in reasoning before yielding visible answer text |
| Dataset access | **BLOCKED** — no local `HF_TOKEN` / `HUGGING_FACE_HUB_TOKEN`; the official runner exited 2 before downloading `cais/hle` |
| Predictions / judging | **Not run** — zero predictions; no accuracy or calibration exists |

Raw, secret-free receipt bundle: `reports/hle_live_20260721T102039Z/`

- `manifest.txt` — evaluator revision, endpoint class, model identifier, and authentication state
- `loopback_models.txt` — OpenAI-model-list response
- `loopback_completion.txt` — live completion response
- `harness.log` + `harness_exit.txt` — official runner’s exact dataset-access stop

The result is a measured access blocker, not an HLE score. The HLE wrapper uses the upstream evaluator’s virtual environment and refuses to invoke its full-set judge for a smoke subset: that upstream judge divides by all 2,500 test questions, so a subset metric would be invalid.

## Resume after dataset authorization

Accept the `cais/hle` access terms, export `HF_TOKEN`, load the listed local model, then run:

```bash
export OPENAI_API_KEY="uum8d-hle-verifier"
export OPENAI_BASE_URL="http://127.0.0.1:8080/v1"
export AFFINE_HARNESS_ENDPOINT="$OPENAI_BASE_URL"
export AFFINE_HARNESS_MODEL="qwen/qwen3.6-35b-a3b"
export HLE_RUN_JUDGE=1
./bin/run-open-agi-harnesses.sh --harness hle
```

Only a complete 2,500-question prediction and judge artifact may add Accuracy or Calibration here. This page intentionally contains no signup or login media.
