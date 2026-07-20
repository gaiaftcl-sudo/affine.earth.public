# Capabilities — What You Can Do with This Rig

![Live language-game surface](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/capabilities-language-game.png)

![MEASURED vs BASELINE](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/banner-measured-vs-baseline.png)

This page is an operational map of features implemented in
`llm-llvm-benchmark-suite`. It distinguishes a command that can run locally
from an outcome that still requires a live model endpoint or an upstream
harness result.

### Product screenshots

| Caption | Image |
|:---|:---|
| Language-game / Franklin chat under Sovereign entry | ![lg](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/capabilities-language-game.png) |
| New wallet path | ![nw](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/sovereign-entry-new-wallet.png) |
| Live healthz | ![hz](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/healthz-json-live.png) |

### Capability tour — public UI + health observation

<p>
<video controls width="720" poster="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/hero-language-game.png">
  <source src="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-signup-healthz.mp4" type="video/mp4">
  <source src="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-signup-healthz.webm" type="video/webm">
</video>
</p>

![Animated walkthrough — Sovereign entry tabs then live healthz JSON](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/demo-signup-healthz.gif)

> **MP4 / WebM:** [https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-signup-healthz.mp4](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-signup-healthz.mp4) · also mirrored at [`docs/media/`](https://github.com/gaiaftcl-sudo/affine.earth.public/tree/main/docs/media) in the public repo.


## Gate — Affine.Earth account (live third-party path)

For any live Affine.Earth session or harness claim against Affine:

1. Complete **[Create Account / Signup](Create-Account-Signup)** (wallet-based Sovereign entry).
2. Obtain a browser session / exported key backup as documented there.
3. Point harnesses only at an endpoint that returns OpenAI-compatible JSON.
4. Optional surface smoke (no fake users): `python3 scripts/check_affine_signup_surface.py`

Local pytest, Clang, and mock-provider wiring do not require an Affine account.

## Local, runnable capabilities

### 1. Verify the package and local compiler path

```bash
python3 -m pytest tests/ -v
python3 scripts/verify_real_numbers_no_flub.py
```

The test suite exercises report generation, LLM evaluation helpers, adapters,
and the local Clang runner. The verification script compiles/runs its C
microbenchmark at `-O0`, `-O2`, `-O3`, and `-Os`, performs exact
numerator/denominator additions, probes the public health endpoint, and writes
`reports/real_verification_proof.json`.

### 2. Measure Clang compile, execution, code size, and IR mix

```bash
python3 -m llm_llvm_bench.cli.main llvm run \
  --opt-levels -O0,-O2,-O3,-Os \
  --compiler clang \
  --out reports/llvm_local.json
```

The runner compiles two bundled C programs:

- `llvm_micro_matrix_mul` — a 200×200 dense matrix multiplication workload.
- `llvm_codesize_sort` — a small bubble-sort code-size workload.

For each optimization level it records compile success, compile time, execution
time, `.text` bytes, total binary size, and a best-effort LLVM IR instruction
breakdown. See [Reports & Artifacts](Reports-And-Artifacts).

### 3. Exercise the LLM evaluator against a real compatible endpoint

```bash
export OPENAI_API_KEY="..."
export OPENAI_BASE_URL="https://your-compatible-host/v1/chat/completions"

python3 -m llm_llvm_bench.cli.main llm run \
  --models your-model-id \
  --provider openai \
  --endpoint "$OPENAI_BASE_URL" \
  --suites code,reasoning,affine_domain \
  --out reports/llm_your_model.json
```

The CLI sends prompts through `OpenAICompatibleProvider`, evaluates returned
code with the package evaluator where test cases exist, and records per-sample
text, pass/fail state, latency, token counts, and errors. `anthropic` uses the
Anthropic Messages API; other provider labels currently route through the
OpenAI-compatible implementation. The exposed suite keys are
`code`, `reasoning`, and `affine_domain`; do not rely on the CLI help text's
stale `tool_use` default.

### 4. Inspect the available prompt set before calling a provider

```bash
python3 - <<'PY'
from llm_llvm_bench.llm.suites import LIST_OF_SUITES
for suite, samples in LIST_OF_SUITES.items():
    print(suite, len(samples))
    for sample in samples:
        print(" ", sample.sample_id, sample.domain)
PY
```

The current package contains three Affine-domain samples (exact rational
addition, constant-time XOR comparison, and an energy-tariff answer), two code
samples, and one reasoning sample. This is a small domain test set, not a
replacement for a large public benchmark.

### 5. Check public service liveness and signup surface

```bash
curl --fail --show-error --silent \
  https://affine.earth/language-invariant/healthz | python3 -m json.tool

python3 scripts/check_affine_signup_surface.py
```

Healthz checks liveness only. The signup script asserts the Sovereign entry HTML
markers (login gate, New wallet, Create wallet + QFOT) without creating an
account. Neither check proves `/v1` chat-completions JSON is available.

### 6. Run the local dashboard

```bash
python3 -m llm_llvm_bench.cli.main serve --host 127.0.0.1 --port 8888
open http://127.0.0.1:8888
curl -sS http://127.0.0.1:8888/api/status | python3 -m json.tool
```

The dashboard and `/api/status` are a local status/demo surface. Its displayed
tables are static in the current implementation; use the JSON files in
`reports/` as benchmark evidence.

### 7. Prepare the hardest public suites without inventing a score

The rig can serve as the artifact and endpoint-validation layer for
Humanity's Last Exam, ARC-AGI, GPQA Diamond, FrontierMath, SWE-bench Verified,
LiveCodeBench, and GAIA. These suites have different upstream distributions
and access terms, so the repository does not pretend one command runs them
all. The stable procedure is:

```bash
# 1. identify the live target; do not begin a score run against HTML
curl --fail --show-error --silent \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  "$OPENAI_BASE_URL/models" | tee reports/provider_models.json

# 2. create an immutable evidence directory for the upstream run
SUITE="swe_bench_verified"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "reports/third_party/$SUITE/$RUN_ID"
git rev-parse HEAD > "reports/third_party/$SUITE/$RUN_ID/harness_commit.txt"
```

Then invoke the official evaluator for the chosen suite, retaining its raw
stdout/stderr, model outputs or patches where allowed, metric JSON, and
checksums. Full acceptance criteria: [Hardest Tests](Hardest-Tests).

## Integration surfaces

| Surface | Implemented use | Evidence to preserve |
|---|---|---|
| Click CLI | LLM and LLVM runs plus local dashboard | command line, generated JSON/Markdown |
| OpenAI-compatible HTTP | prompt/response evaluation | endpoint, model ID, report JSON |
| Anthropic Messages API | prompt/response evaluation | model ID and report JSON |
| Public healthz | liveness probe | raw response and timestamp |
| EleutherAI / BigCode / FastChat | documented upstream invocation paths | upstream-native artifacts, logs, pinned revision |
| HLE / ARC-AGI / GPQA / FrontierMath / SWE-bench / LiveCodeBench / GAIA | hard-suite evidence protocol | official scorer output, task/patch records, pinned revision |
| Local interceptor | HTTP contract development aid | never use its output as a model or harness result |

## Important boundaries

- `llm_llvm_bench/server/affine_v1_interceptor.py` is a local response
  generator. It does not forward requests to Affine.Earth and it is unsuitable
  for a third-party evaluation claim.
- `bin/run-official-leaderboard-harnesses.sh` invokes upstream harness CLIs
  only and fails closed when checkouts, tools, or a JSON `/models` response are
  missing. It does not invent scores or write heredoc result JSON.
- `scripts/run_live_affine_earth_benchmark.py` combines a health probe with
  embedded comparison data. Its comparative output is not a fresh
  third-party-model evaluation.
- The supported, reproducible measured paths today are the local pytest,
  rational/Clang verification, LLVM runner, and any LLM run for which the
  caller retains the actual provider configuration and resulting report.

For upstream reproduction and the current work needed to make it fully
automated, see [Third-Party Harness Reproduction](Third-Party-Harness-Reproduction).
