# Capabilities — What You Can Do with This Rig

This page is an operational map of features implemented in
`llm-llvm-benchmark-suite`. It distinguishes a command that can run locally
from an outcome that still requires a live model endpoint or an upstream
harness result.

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

### 5. Check public service liveness

```bash
curl --fail --show-error --silent \
  https://affine.earth/language-invariant/healthz | python3 -m json.tool
```

This checks that the public health endpoint responded to this request. It does
not establish that an OpenAI chat-completions endpoint is reachable, that a
particular model is deployed, or that any benchmark score was produced.

### 6. Run the local dashboard

```bash
python3 -m llm_llvm_bench.cli.main serve --host 127.0.0.1 --port 8888
open http://127.0.0.1:8888
curl -sS http://127.0.0.1:8888/api/status | python3 -m json.tool
```

The dashboard and `/api/status` are a local status/demo surface. Its displayed
tables are static in the current implementation; use the JSON files in
`reports/` as benchmark evidence.

## Integration surfaces

| Surface | Implemented use | Evidence to preserve |
|---|---|---|
| Click CLI | LLM and LLVM runs plus local dashboard | command line, generated JSON/Markdown |
| OpenAI-compatible HTTP | prompt/response evaluation | endpoint, model ID, report JSON |
| Anthropic Messages API | prompt/response evaluation | model ID and report JSON |
| Public healthz | liveness probe | raw response and timestamp |
| EleutherAI / BigCode / FastChat | documented upstream invocation paths | upstream-native artifacts, logs, pinned revision |
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
