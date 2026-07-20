# Third-party benchmark harnesses

`bin/run-official-leaderboard-harnesses.sh` is a thin launcher for upstream CLIs.
It never starts the local interceptor by itself, never writes heredoc score
JSON, and never invents Pass@k / MT-Bench numbers.

Packaging sources of truth:

| File | Role |
|:---|:---|
| `configs/third-party-harnesses.yaml` | pins, tasks, artifact paths |
| `configs/third-party-harnesses.env.example` | copyable env template |
| `docs/THIRD_PARTY_HARNESSES.md` | this guide |

## Gate 0 — Affine.Earth account (outsiders)

Before claiming a live Affine.Earth harness run:

1. Create or restore a **Sovereign entry** session (wallet-based; not email/password).
   Steps + screenshots: wiki
   [Create Account / Signup](https://github.com/gaiaftcl-sudo/affine.earth.public/wiki/Create-Account-Signup)
   or `wiki/Create-Account-Signup.md`.
2. Smoke the signup UI without creating users:
   `python3 scripts/check_affine_signup_surface.py`
3. Only then point harnesses at a JSON OpenAI-compatible `/v1`.

## Endpoint reality check

As of 2026-07-20:

- `https://affine.earth/language-invariant/healthz` returns HTTP 200 (liveness).
- Signup UI (Sovereign entry) is reachable at `/language-game/` (see Gate 0).
- `https://affine.earth/v1` returns an HTML SPA, **not** OpenAI-compatible JSON.
- `POST /language-invariant/economics-onboard` returned HTTP 404 on an empty-body probe (document; do not treat as successful registration).

Harnesses that call `/v1/models` or `/v1/chat/completions` must target a base
URL that answers `GET …/models` with JSON. The launcher preflights that and
exits non-zero on HTML or non-JSON bodies.

Accepted base-URL env vars (first non-empty wins):

`AFFINE_HARNESS_ENDPOINT` → `AFFINE_OPENAI_BASE_URL` → `OPENAI_BASE_URL` → `AFFINE_BASE_URL`

Local wiring until live `/v1` is JSON (not a public score claim):

```bash
python3 llm_llvm_bench/server/affine_v1_interceptor.py 8000
export AFFINE_HARNESS_ENDPOINT="http://127.0.0.1:8000/v1"
export AFFINE_HARNESS_MODEL="affine-uum8d-s4"
export OPENAI_API_KEY="local-wiring-key"
```

## Configure

```bash
cp configs/third-party-harnesses.env.example .env.third-party-harnesses
$EDITOR .env.third-party-harnesses
# optional: AFFINE_HARNESS_ENV_FILE=.env.third-party-harnesses
./bin/run-official-leaderboard-harnesses.sh --harness lm-eval
```

If `.env.third-party-harnesses` exists in the repo root, the launcher sources it
automatically. Artifacts land under `reports/third_party/` (gitignored).

## EleutherAI lm-evaluation-harness (MMLU, GSM8K)

**Pin:** `lm-eval==0.4.7`

```bash
python3 -m venv .venv/lm-eval
. .venv/lm-eval/bin/activate
python -m pip install --upgrade pip
python -m pip install "lm-eval==0.4.7"

./bin/run-official-leaderboard-harnesses.sh --harness lm-eval
```

Invokes:

```text
lm_eval --model local-chat-completions \
  --model_args model=<MODEL>,base_url=<BASE>/chat/completions,... \
  --tasks mmlu,gsm8k --num_fewshot 0 --batch_size 1 --log_samples \
  --output_path reports/third_party/lm_eval
```

If `lm_eval` is missing, the launcher exits 127 with the install pin above.

## BigCode bigcode-evaluation-harness (HumanEval, MBPP)

**Pin:** git tag `v0.1.0`

```bash
git clone --branch v0.1.0 --depth 1 \
  https://github.com/bigcode-project/bigcode-evaluation-harness.git \
  harnesses/bigcode-evaluation-harness
python3 -m venv .venv/bigcode
. .venv/bigcode/bin/activate
python -m pip install --upgrade pip
python -m pip install -e harnesses/bigcode-evaluation-harness

# Upstream has no native OpenAI-compatible generation backend.
export BIGCODE_LOCAL_MODEL="huggingface-or-local-checkpoint"
./bin/run-official-leaderboard-harnesses.sh --harness bigcode
```

Or score real pre-generated completions (file must already exist):

```bash
export BIGCODE_GENERATIONS_PATH="/absolute/path/generations.json"
./bin/run-official-leaderboard-harnesses.sh --harness bigcode
```

Writes upstream metrics to `reports/third_party/bigcode/results.json`.
`--allow_code_execution` runs untrusted code — use a sandbox.

## LMSYS FastChat MT-Bench

**Pin:** `fschat==0.2.36`

```bash
python3 -m venv .venv/fastchat
. .venv/fastchat/bin/activate
python -m pip install --upgrade pip
python -m pip install "fschat==0.2.36"

./bin/run-official-leaderboard-harnesses.sh --harness fastchat
```

Writes answers to `reports/third_party/fastchat/mt-bench-answers.jsonl`.
Answer generation is not a judge score. Set `MTBENCH_RUN_JUDGE=1` only after
configuring the upstream judge credentials required by FastChat.

## Optional package extra

```bash
python -m pip install -e ".[harnesses]"
```

This installs the pinned `lm-eval` and `fschat` extras from `pyproject.toml`.
BigCode still requires the `v0.1.0` git checkout above.

## Hardest tests / Open AGI

For Humanity's Last Exam, ARC-AGI, GPQA, GAIA, and honest NEEDS_UPSTREAM
pointers (SWE-bench / LiveCodeBench), use the open-AGI launcher and registry:

| File | Role |
|:---|:---|
| `configs/open-agi-harnesses.yaml` | suite IDs (`open_agi_*`) + harness keys |
| `bin/run-open-agi-harnesses.sh` | thin upstream CLI launcher |
| `docs/OPEN_AGI_FRAMEWORKS.md` | framework map, dataset access, blockers |

```bash
./bin/run-open-agi-harnesses.sh --harness gpqa
./bin/run-open-agi-harnesses.sh --harness hle
./bin/run-open-agi-harnesses.sh --harness arc-agi
./bin/run-open-agi-harnesses.sh --harness gaia
./bin/run-open-agi-harnesses.sh --harness swe-bench      # exit 3 NEEDS_UPSTREAM
./bin/run-open-agi-harnesses.sh --harness livecodebench  # exit 3 NEEDS_UPSTREAM
```

Same fail-loud rules: no heredoc scores, JSON `/models` preflight where the
upstream path is OpenAI-compatible.

## Provenance rule

A score is **MEASURED** only when you retain the upstream artifact, exact
command, pin/revision, model id, and base URL class (no secrets). Healthz alone
is not benchmark evidence. Local interceptor output is wiring evidence only.
