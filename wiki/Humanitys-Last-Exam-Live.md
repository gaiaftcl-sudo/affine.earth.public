# Humanity’s Last Exam — live harness record

Official sources: [agi.safe.ai](https://agi.safe.ai/), the [CAIS HLE evaluator](https://github.com/centerforaisafety/hle), and the gated [cais/hle dataset](https://huggingface.co/datasets/cais/hle).

## Recorded 2026-07-21 (live rerun)

| Check | Observed result |
|:---|:---|
| Affine loopback | `http://127.0.0.1:8080/v1/models` returned OpenAI JSON with `qwen/qwen3.6-35b-a3b` and `text-embedding-nomic-embed-text-v1.5` |
| Environment token check | `HF_TOKEN` and `HUGGING_FACE_HUB_TOKEN` were absent; no Keychain or `security` command was used |
| Anonymous dataset download | `https://huggingface.co/datasets/cais/hle/resolve/main/test-00000-of-00001.parquet` returned **HTTP 401 Unauthorized** |
| Official CAIS runner | `./bin/run-open-agi-harnesses.sh --harness hle` exited **2** before prediction, with `HLE_RUN_JUDGE=1` and the live loopback endpoint |
| Predictions / judging | **Not run** — the official runner requires a Hub access token after terms authorization; therefore no Accuracy or Calibration exists |

Secret-free receipt bundle: `reports/hle_live_20260721T103322Z/` (`proxy_models.json`, `hle_runner.log`, and `receipt.txt`).

No screenshot or video was created: no evaluator UI or model evaluation began.

## Recorded 2026-07-21 (auth re-probe)

| Check | Observed result |
|:---|:---|
| CAIS evaluator | Cloned at `26dca2e253b405105b4c3d8c2f5af06f86f90c66`; isolated `hle_eval/.venv` installed from the upstream root `requirements.txt` |
| Affine loopback | `http://127.0.0.1:8080/v1/models` returned OpenAI JSON (`qwen/qwen3.6-35b-a3b`) through the live transparent loopback proxy |
| Local classic `HF_TOKEN` | **Absent** — not in env, shell profiles, `~/.cache/huggingface/token`, Keychain generic HF items, `.env` files, 1Password CLI, or `gh secret list` |
| Recovered Hub identity | Cursor HF MCP OAuth for Hub user `rpg67` (session-only; never committed). `whoami` HTTP 200 |
| Dataset gate | `cais/hle` is `gated=auto`. Repo tree lists `data/test-00000-of-00001.parquet`, but parquet resolve returns **HTTP 403** (“not in the authorized list”) for both OAuth and HF MCP `hf_fs` |
| Terms accept API | `POST /datasets/cais/hle/ask-access` with the MCP OAuth bearer returned **401** (web gate accept requires a browser session / classic user access token after accepting terms) |
| Predictions / judging | **Not run** — zero predictions; no accuracy or calibration exists |

Secret-free receipts:

- Earlier harness stop (no token in env): `reports/hle_live_20260721T102039Z/`
- Auth re-probe (OAuth found, parquet still gated): `reports/hle_live_20260721T102858Z/`

This is a measured **steward gate**, not an HLE score. Accuracy/Calibration can only be written after a successful official CAIS prediction + judge artifact.

## Steward steps (required before any HLE score)

1. In a browser, log in as Hub user **`rpg67`** (or another account you intend to use for the harness).
2. Open [https://huggingface.co/datasets/cais/hle](https://huggingface.co/datasets/cais/hle) and accept the gated-dataset access / terms (click **Agree** / **Access repository** until the page shows you are authorized).
3. Create a **classic** user access token (Read is enough) at [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) — do not paste it into wiki, git, or chat logs.
4. In the harness shell only:
   ```bash
   export HF_TOKEN="hf_..."   # classic token; session only
   # optional: huggingface-cli login
   ```
5. Confirm parquet access (expect HTTP 200 / `PAR1` magic), then run:
   ```bash
   export OPENAI_API_KEY="uum8d-hle-verifier"
   export OPENAI_BASE_URL="http://127.0.0.1:8080/v1"
   export AFFINE_HARNESS_ENDPOINT="$OPENAI_BASE_URL"
   export AFFINE_HARNESS_MODEL="qwen/qwen3.6-35b-a3b"
   export HLE_RUN_JUDGE=1
   ./bin/run-open-agi-harnesses.sh --harness hle
   ```

Only a complete 2,500-question prediction and judge artifact may add Accuracy or Calibration here. Never commit `HF_TOKEN`, Kaggle tokens, or OAuth secrets.
