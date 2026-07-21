# Humanity’s Last Exam — live harness record

Official sources: [agi.safe.ai](https://agi.safe.ai/), the [CAIS HLE evaluator](https://github.com/centerforaisafety/hle), and the gated [cais/hle dataset](https://huggingface.co/datasets/cais/hle).

## Local mastery (aligned to language-game invariants)

Doctrine: [`docs/LANGUAGE_GAMES_HLE.md`](../docs/LANGUAGE_GAMES_HLE.md) (SHA `f983986`) · wiki: [Language-Games-HLE](Language-Games-HLE) · shared gate: [Exam invariants](Language-Games-Exam-Invariants).

**2026-07-21 update:** `load_dataset("cais/hle")` succeeded after steward-provided classic `HF_TOKEN` (process env / hub cache only — never committed). Split lengths: **`test=2500`**. Full predict+judge is in flight under `reports/hle_official_20260721T143509Z/` (`official_hle_accuracy` remains **null** until judged JSON + receipt). Local fixture matches stay local evidence only. No Keychain. **Rotate the HF token** that was pasted in chat after the exam run.

```bash
export OPENAI_BASE_URL="http://127.0.0.1:8080/v1"
export OPENAI_API_KEY="uum8d-hle-verifier"
./bin/run-local-hle-mastery.sh
```

### UI captures (interaction evidence, not scores)

Local drill receipt: [`reports/hle_local_20260721T104720Z/`](https://github.com/gaiaftcl-sudo/affine.earth.public/tree/main/reports/hle_local_20260721T104720Z) (`official_hle_accuracy: null`, fixtures **3/3**, `HF_TOKEN` absent). Doctrine SHA `f983986` · main harness SHA `c3cf4d3`.

![HLE access gate](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-access-gate.png)

![HLE games catalog](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-games-catalog.png)

| Layer | Still → answer |
|:---|:---|
| Linguistic membrane | ![still](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-linguistic_membrane.png) ![answer](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-linguistic_membrane-answer.png) |
| Formal manifold | ![still](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-formal_manifold.png) ![answer](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-formal_manifold-answer.png) |
| Coding | ![still](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-coding.png) ![answer](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-coding-answer.png) |

Context → answer motion (not a signup/login walkthrough; that video lives only on [Create account](Create-Account-Signup)):

![HLE context to answer](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-context-to-answer.gif)

<video controls width="720">
  <source src="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-context-to-answer.mp4" type="video/mp4">
</video>

[mp4](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-context-to-answer.mp4) · [gif](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-context-to-answer.gif)

## Recorded 2026-07-21 (steward reset redo)

Steward closed the browser and requested a full clean redo. Cleanup intentionally cleared `:8080`; this session restarted the OpenAI JSON loopback proxy and re-probed dataset access. **No Keychain / `security` CLI.**

| Check | Observed result |
|:---|:---|
| Loopback proxy | Restarted on `127.0.0.1:8080` → upstream `http://127.0.0.1:1234`; `GET /v1/models` → **HTTP 200** OpenAI JSON (`qwen/qwen3.6-35b-a3b`) — PID recorded in receipt |
| Classic `HF_TOKEN` | **Absent** in harness shell env (`HF_TOKEN` / `HUGGING_FACE_HUB_TOKEN` unset; no `~/.cache/huggingface/token`) |
| Hub identity (MCP OAuth) | `hf_whoami` → user **`rpg67`** (session-only; never committed) |
| Dataset gate | `GET https://huggingface.co/api/datasets/cais/hle` → `gated=auto`, `private=false` |
| Parquet resolve (no token) | `.../resolve/main/data/test-00000-of-00001.parquet` → **HTTP 401** (“Access to dataset cais/hle is restricted… Please log in.”); magic ≠ `PAR1` |
| MCP `hf_fs` | `stat` sees LFS parquet (~274.3 MB); binary `cat` refused by tool — resolve still requires classic auth after Agree |
| System browser | Opened once to [cais/hle](https://huggingface.co/datasets/cais/hle) for steward **Agree** + token export |
| Predictions / judging | **Not run** — zero predictions; no Accuracy or Calibration |

Receipts (secret-free):

- Fresh redo probe + proxy restart: `reports/hle_live_20260721T103415Z/`
- Prior unauth probe: `reports/hle_live_20260721T103340Z_unauth/`
- Earlier auth re-probe: `reports/hle_live_20260721T102858Z/`
- Earlier harness stop (no token): `reports/hle_live_20260721T102039Z/`

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
