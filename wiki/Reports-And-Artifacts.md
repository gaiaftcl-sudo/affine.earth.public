# Reports & Artifacts

Every benchmark claim should be traceable to a command, generated artifact,
environment description, and source revision. This page describes the report
formats produced by the code in this repository.

## Artifact inventory

| File or directory | Producer | What it can establish |
|---|---|---|
| `reports/real_verification_proof.json` | `scripts/verify_real_numbers_no_flub.py` | local Clang/rational checks and one healthz request |
| `reports/llvm_*.json` + `.md` | `llm-llvm-bench llvm run` | local compiler benchmark results |
| `reports/llm_*.json` + `.md` | `llm-llvm-bench llm run` | a particular provider/model invocation |
| `reports/affine_earth_vs_frontier_models.*` | `run_live_affine_earth_benchmark.py` | health probe plus embedded comparison table |
| `reports/affine-results/` | EleutherAI CLI, when invoked directly | lm-eval artifacts |
| `reports/official_harness_logs/` | caller-created logs | command stdout/stderr |

`affine-bigcode-results.json` and `affine-mt-bench-results.json` need special
handling: the current wrapper writes their contents directly. Treat them as
schema examples until direct upstream execution overwrites them and you retain
that execution's logs.

## `BenchmarkReport` JSON

The CLI serializes the dataclasses in `llm_llvm_bench/core/types.py`.

```json
{
  "report_id": "llvm_run_...",
  "created_at": 0,
  "llm_suites": [],
  "llvm_suites": []
}
```

`created_at` and individual suite `timestamp` fields are Unix seconds.
`report_id` is generated from the current Unix time; it identifies the file
generation event but is not a cryptographic content hash.

### LLM suite fields

Each `llm_suites[]` object contains:

- `suite_name`, `model_name`
- `total_samples`, `passed_samples`, `accuracy_pct`
- `avg_latency_sec`, `tokens_per_sec`, `timestamp`
- `results[]`, one record per prompt

Every result records `sample_id`, `domain`, `prompt`, `generated_text`,
`passed`, `latency_sec`, token counts, `error_message`, and free-form
`metadata`. `passed` means the package evaluator accepted that response for
that sample; it is not a general security, quality, or upstream-harness
certification.

Inspect a compact summary:

```bash
python3 - <<'PY'
import json, sys
p = json.load(open(sys.argv[1]))
for suite in p["llm_suites"]:
    print(suite["model_name"], suite["suite_name"],
          f'{suite["passed_samples"]}/{suite["total_samples"]}',
          f'{suite["accuracy_pct"]:.1f}%',
          f'{suite["avg_latency_sec"]:.3f}s')
PY reports/llm_your_model.json
```

Find failed or transport-error samples:

```bash
python3 - <<'PY'
import json, sys
p = json.load(open(sys.argv[1]))
for suite in p["llm_suites"]:
    for result in suite["results"]:
        if not result["passed"] or result["error_message"]:
            print(result["sample_id"], result["error_message"] or "evaluation failed")
PY reports/llm_your_model.json
```

### LLVM suite fields

Each `llvm_suites[]` object contains:

- `suite_name`, `compiler_name`, `opt_level`
- `total_samples`, `compiled_samples`
- `avg_compile_time_sec`, `avg_execution_time_sec`
- `total_text_size_bytes`, `timestamp`
- `results[]`, one record per C workload

Each result records `compile_success`, compile/execution times, code-size
fields, `ir_instruction_count`, and `error_message`.

```bash
python3 - <<'PY'
import json, sys
p = json.load(open(sys.argv[1]))
for suite in p["llvm_suites"]:
    print(suite["opt_level"],
          f'{suite["compiled_samples"]}/{suite["total_samples"]}',
          f'compile={suite["avg_compile_time_sec"]:.4f}s',
          f'exec={suite["avg_execution_time_sec"]:.4f}s',
          f'text={suite["total_text_size_bytes"]}B')
    for result in suite["results"]:
        print(" ", result["sample_id"], "success=", result["compile_success"],
              "error=", result["error_message"])
PY reports/llvm_local.json
```

Compare matched optimization levels without modifying either receipt:

```bash
python3 - <<'PY'
import json, sys
before, after = (json.load(open(path)) for path in sys.argv[1:3])
def index(report):
    return {row["opt_level"]: row for row in report["llvm_suites"]}
for opt in sorted(set(index(before)) & set(index(after))):
    a, b = index(before)[opt], index(after)[opt]
    print(opt,
          "compile_delta_sec=", b["avg_compile_time_sec"] - a["avg_compile_time_sec"],
          "exec_delta_sec=", b["avg_execution_time_sec"] - a["avg_execution_time_sec"])
PY reports/llvm_before.json reports/llvm_after.json
```

## Verification-script receipt

`real_verification_proof.json` is a separate JSON schema. Its key sections
are:

- `clang_compilation_real_metrics`: per-optimization-level timings, sizes, and
  program output.
- `rational_arithmetic_real_metrics`: exact addition iteration count, elapsed
  time, and the script's `float_drift` field.
- `live_probe_metrics`: the health request status, latency, and liveness flag.
- `proven_status`: completion stamp written by the script.

The health probe is a single network observation. Retain the raw HTTP body if
its feature flags are material to a report:

```bash
curl -sS -D reports/healthz_headers.txt \
  https://affine.earth/language-invariant/healthz \
  -o reports/healthz_body.json
shasum -a 256 reports/healthz_headers.txt reports/healthz_body.json
```

## Reproducible evidence bundle

Create a bundle after an actual run:

```bash
git rev-parse HEAD > reports/source_commit.txt
python3 --version > reports/environment.txt
clang --version >> reports/environment.txt
uname -a >> reports/environment.txt
shasum -a 256 reports/*.json reports/*.md > reports/SHA256SUMS.txt
tar -czf "/tmp/affine-artifacts-$(date -u +%Y%m%dT%H%M%SZ).tgz" reports/
```

For a remote provider or upstream harness, also retain:

1. exact command line (with secrets removed);
2. endpoint host and model ID;
3. dependency lockfile or `pip freeze`;
4. upstream repository commit;
5. stdout/stderr logs; and
6. the raw upstream-native result files.

See [Third-Party Harness Reproduction](Third-Party-Harness-Reproduction) for
the upstream-harness bundle layout.
