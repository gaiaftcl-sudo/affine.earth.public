# Affine.Earth Public Benchmark Rig

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](pyproject.toml)
[![Tests: 10](https://img.shields.io/badge/tests-10-green.svg)](tests/)

An installable, reproducible rig for measuring LLM API behaviour and local LLVM
compiler behaviour. It produces local JSON and Markdown reports; it does not
ship precomputed scores as new measurements.

## What this repository runs

- **Unit and verification checks**: Python tests plus real local `clang` compile
  and execution measurements.
- **LLM suites**: the bundled `affine_domain`, `code`, and `reasoning` samples
  against an explicitly configured provider endpoint.
- **LLVM suite**: local `clang` measurements at `-O0`, `-O2`, `-O3`, and `-Os`.
- **Third-party harnesses**: installed upstream `lm-evaluation-harness`,
  BigCode evaluation harness, and FastChat. Their outputs remain in
  `reports/third_party/`.

## Install

Requirements: Python 3.9+, `clang` on `PATH`, and `size` (or an equivalent
platform tool accepted by your local LLVM installation).

```bash
git clone https://github.com/gaiaftcl-sudo/affine.earth.public.git
cd affine.earth.public
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

For optional upstream harness clients (pinned extras + BigCode checkout):

```bash
python -m pip install -e ".[dev,harnesses]"   # lm-eval==0.4.7, fschat==0.2.36
git clone --branch v0.1.0 --depth 1 \
  https://github.com/bigcode-project/bigcode-evaluation-harness.git \
  harnesses/bigcode-evaluation-harness
python -m pip install -e harnesses/bigcode-evaluation-harness
```

Exact pins, env aliases, and outsider run commands:
[docs/THIRD_PARTY_HARNESSES.md](docs/THIRD_PARTY_HARNESSES.md) ·
[configs/third-party-harnesses.yaml](configs/third-party-harnesses.yaml).

**Endpoint note:** `https://affine.earth/v1` currently returns an HTML SPA, not
OpenAI JSON. Point `OPENAI_BASE_URL` / `AFFINE_HARNESS_ENDPOINT` at a real
OpenAI-compatible `/v1` (or a local interceptor for wiring only).

## Configure an LLM endpoint

Configuration is environment based so secrets never enter reports or git:

```bash
cp configs/affine-earth.env.example .env.affine-earth
cp configs/providers.env.example .env.providers
cp configs/suites.env.example .env.suites
$EDITOR .env.affine-earth .env.providers .env.suites
set -a
source .env.affine-earth
source .env.providers
source .env.suites
set +a
```

Set `AFFINE_ENDPOINT` to the OpenAI-compatible `/chat/completions` URL, choose
`AFFINE_MODEL`, and provide `OPENAI_API_KEY` only when the endpoint requires
one. No live LLM request is made unless you pass `--live`.

## Commands

```bash
# Local checks only: pytest + real clang/rational verification.
./bin/verify-rig.sh

# Full local rig: verification + LLVM measurement.
./bin/run-full-benchmark.sh

# Full rig plus configured live LLM suite.
./bin/run-full-benchmark.sh --live

# Run the bundled LLM suites directly.
llm-llvm-bench llm run \
  --models "$AFFINE_MODEL" \
  --provider openai \
  --endpoint "$AFFINE_ENDPOINT" \
  --suites "$AFFINE_SUITES" \
  --out reports/llm_benchmark.json

# LLVM only.
llm-llvm-bench llvm run --compiler clang --opt-levels -O0,-O2,-O3,-Os

# Upstream harnesses (fail loudly if CLI/checkout/JSON /models is missing).
cp configs/third-party-harnesses.env.example .env.third-party-harnesses
# Edit endpoint + model; do not leave https://affine.earth/v1 until it returns JSON.
./bin/run-official-leaderboard-harnesses.sh --harness lm-eval
./bin/run-official-leaderboard-harnesses.sh --harness bigcode
./bin/run-official-leaderboard-harnesses.sh --harness fastchat
```

`bin/run-official-leaderboard-harnesses.sh` never invents scores and never
writes heredoc receipts. It sources `.env.third-party-harnesses` when present,
preflights `GET $BASE/models` for JSON, invokes the upstream CLI, or exits with
install pins from `configs/third-party-harnesses.yaml`.

## Reports and provenance

Generated reports are ignored by git under `reports/`. Each run should retain:

- command line and configuration values that are safe to disclose,
- timestamp, tool versions, task/suite selection, and raw upstream artifacts,
- endpoint and model identifiers, and
- an explicit provenance label:
  - **MEASURED**: created by this run from a reachable endpoint or local tool;
  - **BASELINE**: an externally cited historical result, not a new result from
    this repository.

Do not compare, publish, or submit a score without the corresponding raw
artifact and exact command. See [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

## Layout

```text
bin/        reproducible entrypoints
configs/    copyable environment templates
docs/       methodology and reproduction notes
llm_llvm_bench/
  llm/      provider clients and bundled suites
  llvm/     local compiler benchmark runner
scripts/    verification and live-report helpers
tests/      10 pytest tests
```

## Contributing and license

Read [CONTRIBUTING.md](CONTRIBUTING.md) for reproducible change and report
requirements. Released under the [MIT License](LICENSE).
