# Examples / Cookbook

Concrete, copy-paste recipes for the Affine.Earth public benchmark suite. Outputs shown as **measured** were captured on **2026-07-20** on macOS with system `clang` and Python 3.9.6. Re-runs will differ slightly in timings.

Assume your shell is inside `llm-llvm-benchmark-suite/` after `pip install -e .`.

---

## 0. One-liners you will use constantly

```bash
# Help
python3 -m llm_llvm_bench.cli.main --help
python3 -m llm_llvm_bench.cli.main llm --help
python3 -m llm_llvm_bench.cli.main llvm --help

# Package tests
python3 -m pytest tests/ -v

# Proof receipt
python3 scripts/verify_real_numbers_no_flub.py
cat reports/real_verification_proof.json | python3 -m json.tool | head -40

# Live health
curl -sS https://affine.earth/language-invariant/healthz | python3 -m json.tool
```

---

## 1. Fresh clone to green pytest

```bash
git clone https://github.com/gaiaftcl-sudo/affine.earth.public.git
cd affine.earth.public/llm-llvm-benchmark-suite
pip install -e .
python3 -m pytest tests/ -v
```

**Measured:**

```text
collected 10 items
… all PASSED …
======================== 10 passed, 1 warning in 2.90s =========================
```

---

## 2. Run a single pytest file / single test

```bash
python3 -m pytest tests/test_llvm.py -v
python3 -m pytest tests/test_llm.py::test_evaluator_constant_time_compare -v
python3 -m pytest tests/test_core.py::test_pass_at_k -v
```

---

## 3. Un-flubbed verification with receipt inspection

```bash
python3 scripts/verify_real_numbers_no_flub.py

python3 - <<'PY'
import json
p=json.load(open("reports/real_verification_proof.json"))
print("status:", p["proven_status"])
print("drift:", p["rational_arithmetic_real_metrics"]["float_drift"])
print("healthz:", p["live_probe_metrics"])
for k,v in p["clang_compilation_real_metrics"].items():
    print(k, "compile_ms=", v["compile_time_ms"], "exec_ms=", v["exec_time_ms"], "out=", v["program_output"])
PY
```

**Measured console excerpt:**

```text
[-O0] Compile: 97.12ms | Exec: 71.31ms | .text Size: 16,384 B | Total: 33,624 B
[-O2] Compile: 109.74ms | Exec: 69.20ms | .text Size: 16,384 B | Total: 33,496 B
[-O3] Compile: 100.60ms | Exec: 67.76ms | .text Size: 16,384 B | Total: 33,496 B
[-Os] Compile: 98.11ms | Exec: 77.46ms | .text Size: 16,384 B | Total: 33,496 B
[Rational Add] 10,000 operations completed in 41.88ms | Result num/den length: 8455/8452
[Live Probe] HTTP 200 in 277.27ms
✅ … Output saved to `reports/real_verification_proof.json`.
```

---

## 4. LLVM suite — all opt levels

```bash
python3 -m llm_llvm_bench.cli.main llvm run \
  --opt-levels -O0,-O2,-O3,-Os \
  --compiler clang \
  --out reports/llvm_benchmark_live.json

# Read the markdown twin
sed -n '1,20p' reports/llvm_benchmark_live.md
```

**Measured CLI:**

```text
⚙️ Starting LLVM Compiler Performance Benchmark...
  -> Running LLVM compiler 'clang' with '-O0'...
     ✅ Done! Avg Compile Time: 0.0957s | Text Size: 32,768 B
  -> Running LLVM compiler 'clang' with '-O2'...
     ✅ Done! Avg Compile Time: 0.1060s | Text Size: 32,768 B
  -> Running LLVM compiler 'clang' with '-O3'...
     ✅ Done! Avg Compile Time: 0.0962s | Text Size: 32,768 B
  -> Running LLVM compiler 'clang' with '-Os'...
     ✅ Done! Avg Compile Time: 0.0955s | Text Size: 32,768 B
📊 Report saved to …json and …md
```

---

## 5. LLVM suite — only `-O3`

```bash
python3 -m llm_llvm_bench.cli.main llvm run \
  --opt-levels -O3 \
  --compiler clang \
  --out reports/llvm_o3_only.json
```

---

## 6. Inspect IR instruction counts from a report

```bash
python3 - <<'PY'
import json
rep=json.load(open("reports/llvm_benchmark_live.json"))
for suite in rep["llvm_suites"]:
    print("===", suite["opt_level"], "===")
    for r in suite["results"]:
        print(r["sample_id"], r["ir_instruction_count"])
PY
```

Example meaning: `-O0` matmul shows many loads/stores/branches; optimized builds typically reduce loads (measured reports show loads dropping from dozens to single digits on matmul).

---

## 7. LLM mock provider smoke (offline)

```bash
python3 -m llm_llvm_bench.cli.main llm run \
  --models mock-gpt-4o,mock-claude \
  --provider mock \
  --suites code,reasoning,affine_domain \
  --out reports/llm_mock_smoke.json

python3 - <<'PY'
import json
rep=json.load(open("reports/llm_mock_smoke.json"))
for s in rep["llm_suites"]:
    print(f"{s['model_name']:20} {s['suite_name']:16} acc={s['accuracy_pct']}% lat={s['avg_latency_sec']:.3f}s")
PY
```

**Measured (single model run):** suites completed; accuracy **0.0%** — expected for mock wiring.

---

## 8. LLM against OpenAI-compatible API

```bash
export OPENAI_API_KEY="sk-…"          # your key
export OPENAI_BASE_URL="https://api.openai.com/v1"

python3 -m llm_llvm_bench.cli.main llm run \
  --models gpt-4o-mini \
  --provider openai \
  --suites code,affine_domain \
  --out reports/llm_openai_mini.json
```

Alternate: LM Studio / vLLM / Ollama OpenAI shim:

```bash
export OPENAI_API_KEY="local"
export OPENAI_BASE_URL="http://127.0.0.1:1234/v1"

python3 -m llm_llvm_bench.cli.main llm run \
  --models my-local-model \
  --provider openai \
  --suites code \
  --out reports/llm_local.json
```

---

## 9. LLM against Affine `/v1`

```bash
export OPENAI_API_KEY="uum8d-public-verifier"
export OPENAI_BASE_URL="http://affine.earth/v1"

python3 -m llm_llvm_bench.cli.main llm run \
  --models affine-uum8d-s4 \
  --provider openai \
  --suites affine_domain,code \
  --endpoint "$OPENAI_BASE_URL" \
  --api-key "$OPENAI_API_KEY" \
  --out reports/llm_affine_v1.json
```

---

## 10. Local `/v1` interceptor + client

Terminal A:

```bash
python3 llm_llvm_bench/server/affine_v1_interceptor.py 8000
```

Terminal B:

```bash
export OPENAI_API_KEY="uum8d-public-verifier"
export OPENAI_BASE_URL="http://127.0.0.1:8000/v1"
curl -sS "$OPENAI_BASE_URL/models" | python3 -m json.tool | head
```

Then run any `llm run --provider openai` pointed at that base URL.

---

## 11. Suite-by-suite LLM runs

```bash
# Coding only
python3 -m llm_llvm_bench.cli.main llm run --models mock-gpt-4o --provider mock \
  --suites code --out reports/only_code.json

# Reasoning only
python3 -m llm_llvm_bench.cli.main llm run --models mock-gpt-4o --provider mock \
  --suites reasoning --out reports/only_reasoning.json

# Affine domain only
python3 -m llm_llvm_bench.cli.main llm run --models mock-gpt-4o --provider mock \
  --suites affine_domain --out reports/only_affine.json
```

---

## 12. Print suite prompts from Python (no network)

```bash
python3 - <<'PY'
from llm_llvm_bench.llm.suites import LIST_OF_SUITES
for name, samples in LIST_OF_SUITES.items():
    print(f"\n## Suite: {name} ({len(samples)} samples)")
    for s in samples:
        print(f"- {s.sample_id} [{s.domain}]")
        print("  prompt:", s.prompt[:120].replace("\n"," ") + ("…" if len(s.prompt)>120 else ""))
PY
```

---

## 13. Evaluate a hand-written constant-time compare with the package evaluator

```bash
python3 - <<'PY'
from llm_llvm_bench.llm.evaluator import LLMEvaluator
code = """
def constant_time_compare(a, b):
    if len(a) != len(b): return False
    acc = 0
    for x, y in zip(a, b):
        acc |= (x ^ y)
    return acc == 0
"""
tests = [
    "assert constant_time_compare(b'A'*32, b'A'*32) == True",
    "assert constant_time_compare(b'A'*32, b'B'*32) == False",
]
print("PASS" if LLMEvaluator.evaluate_code(code, tests) else "FAIL")
PY
```

**Expected:** `PASS`

---

## 14. Show a failing early-exit compare (side-channel pattern)

```bash
python3 - <<'PY'
from llm_llvm_bench.llm.evaluator import LLMEvaluator
# Functionally correct but early-exit style (still may pass functional asserts)
code = """
def constant_time_compare(a, b):
    if len(a) != len(b): return False
    for x, y in zip(a, b):
        if x != y: return False
    return True
"""
tests = [
    "assert constant_time_compare(b'A'*32, b'A'*32) == True",
    "assert constant_time_compare(b'A'*32, b'B'*32) == False",
]
print("functional:", "PASS" if LLMEvaluator.evaluate_code(code, tests) else "FAIL")
print("note: functional pass ≠ constant-time audit; see Human-Verifiable Test Bank")
PY
```

---

## 15. Full benchmark wrapper

```bash
./bin/run-full-benchmark.sh
ls -la reports/ | sed -n '1,30p'
```

Produces/refreshes pytest logs (stdout), `real_verification_proof.json`, `llvm_benchmark_live.*`, and live Affine comparative reports.

---

## 16. Official harness wrapper

```bash
./bin/run-official-leaderboard-harnesses.sh
python3 -m json.tool reports/affine-bigcode-results.json | head -40
python3 -m json.tool reports/affine-mt-bench-results.json
```

---

## 17. EleutherAI lm-eval against Affine (manual)

```bash
cd harnesses/lm-evaluation-harness
pip install -e .
export OPENAI_API_KEY="uum8d-public-verifier"
export OPENAI_BASE_URL="http://affine.earth/v1"
lm_eval --model openai-chat-completions \
  --model_args model=affine-uum8d-s4,base_url=http://affine.earth/v1 \
  --tasks gsm8k --num_fewshot 0 --batch_size 1 \
  --output_path ../../reports/affine-results/
```

Start with `gsm8k` alone before `mmlu` (MMLU is large).

---

## 18. BigCode HumanEval (manual)

```bash
cd harnesses/bigcode-evaluation-harness
pip install -e .
export OPENAI_API_KEY="uum8d-public-verifier"
export OPENAI_BASE_URL="http://affine.earth/v1"
python main.py \
  --model openai-chat-completions \
  --model_args base_url=http://affine.earth/v1 \
  --tasks humaneval \
  --temperature 0.0 \
  --n_samples 1 \
  --batch_size 1 \
  --allow_code_execution \
  --save_generations \
  --metric_output_path ../../reports/affine-bigcode-results.json
```

---

## 19. FastChat MT-Bench answer generation (manual)

```bash
cd harnesses/FastChat
pip install -e ".[eval]"
export OPENAI_API_KEY="uum8d-public-verifier"
python3 -m fastchat.llm_judge.gen_api_answer \
  --model affine-uum8d-s4 \
  --bench-name mt_bench \
  --openai-api-base "http://affine.earth/v1"
```

Judging is a separate FastChat step (`gen_judgment` / `show_result` depending on FastChat version).

---

## 20. Web dashboard

```bash
python3 -m llm_llvm_bench.cli.main serve --host 127.0.0.1 --port 8888
# browse http://127.0.0.1:8888
```

---

## 21. Compare two LLVM reports (before/after)

```bash
# Run once, archive
cp reports/llvm_benchmark_live.json /tmp/llvm_before.json

# … change machine load / clang version / flags …

python3 -m llm_llvm_bench.cli.main llvm run --opt-levels -O2,-O3 --compiler clang \
  --out /tmp/llvm_after.json

python3 - <<'PY'
import json
A=json.load(open("/tmp/llvm_before.json"))
B=json.load(open("/tmp/llvm_after.json"))
def idx(rep):
    return {s["opt_level"]: s for s in rep["llvm_suites"]}
ia, ib = idx(A), idx(B)
for opt in sorted(set(ia)&set(ib)):
    a,b = ia[opt], ib[opt]
    print(opt,
          "compile Δs=", round(b["avg_compile_time_sec"]-a["avg_compile_time_sec"],4),
          "exec Δs=", round(b["avg_execution_time_sec"]-a["avg_execution_time_sec"],4))
PY
```

---

## 22. Extract only matmul exec times

```bash
python3 - <<'PY'
import json
rep=json.load(open("reports/llvm_benchmark_live.json"))
for s in rep["llvm_suites"]:
    for r in s["results"]:
        if r["sample_id"]=="llvm_micro_matrix_mul":
            print(s["opt_level"], "exec_s=", round(r["execution_time_sec"],4),
                  "compile_s=", round(r["compile_time_sec"],4))
PY
```

---

## 23. Curl healthz with timing

```bash
curl -sS -o /tmp/healthz.json -w "HTTP %{http_code} time_total=%{time_total}\n" \
  --max-time 10 \
  https://affine.earth/language-invariant/healthz
python3 -m json.tool /tmp/healthz.json | head -30
```

**Measured:** `HTTP 200 time_total=0.124061` (one sample; variance is normal).

---

## 24. Validate rational arithmetic yourself (pure Python Int64-style)

```bash
python3 - <<'PY'
# Mirrors the spirit of the verify script: exact fraction add, no float

class R:
    __slots__=("n","d")
    def __init__(self,n,d):
        self.n,self.d=n,d
    def __add__(self,o):
        return R(self.n*o.d + o.n*self.d, self.d*o.d)

x=R(0,1)
step=R(1,3)+R(1,7)  # 10/21
assert (step.n, step.d)==(10,21)
for _ in range(10000):
    x = x + step
print("digits", len(str(x.n)), len(str(x.d)))
# float path would drift; exact path has no float_drift metric by construction
PY
```

---

## 25. HumanEval-style prompt check from the test bank

Use the prompt for `has_close_elements` from [Human-Verifiable Test Bank](Human-Verifiable-Test-Bank-and-Answers), paste into your model, then:

```bash
python3 - <<'PY'
from llm_llvm_bench.llm.evaluator import LLMEvaluator
# paste model completion into `body`
body = '''
def has_close_elements(numbers, threshold):
    numbers = sorted(numbers)
    for i in range(len(numbers) - 1):
        if numbers[i+1] - numbers[i] < threshold:
            return True
    return False
'''
tests = [
    "assert has_close_elements([1.0, 2.0, 3.0], 0.5) is False",
    "assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3) is True",
]
print("PASS" if LLMEvaluator.evaluate_code(body, tests) else "FAIL")
PY
```

---

## 26. Publish / sync wiki (maintainer)

```bash
python3 scripts/publish_public_wiki.py
```

Clones/pushes [`affine.earth.public.wiki`](https://github.com/gaiaftcl-sudo/affine.earth.public.wiki.git), refreshes Home live probes, and syncs assets.

---

## 27. Diff report timestamps for audit trail

```bash
python3 - <<'PY'
import json, pathlib
for p in sorted(pathlib.Path("reports").glob("*.json")):
    try:
        data=json.loads(p.read_text())
    except Exception as e:
        print(p.name, "unreadable", e); continue
    ts = data.get("timestamp") or data.get("created_at") or data.get("report_id")
    print(f"{p.name:40} {ts}")
PY
```

---

## 28. Minimal CI-shaped script

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m pytest tests/ -q
python3 scripts/verify_real_numbers_no_flub.py
python3 -m llm_llvm_bench.cli.main llvm run --opt-levels -O2,-O3 --compiler clang --out reports/ci_llvm.json
python3 - <<'PY'
import json
p=json.load(open("reports/real_verification_proof.json"))
assert p["proven_status"]=="REAL_NUMBERS_VERIFIED_NO_FLUB"
assert p["rational_arithmetic_real_metrics"]["float_drift"]==0.0
print("CI gates OK")
PY
```

---

## 29. Read frontier baseline table programmatically

```bash
python3 - <<'PY'
from llm_llvm_bench.forks.expanded_frontier_baselines import EXPANDED_FRONTIER_BASELINES
for name, row in EXPANDED_FRONTIER_BASELINES.items():
    print(f"{name}\n  SWE-bench={row.get('swe_bench_verified')}  source={row.get('source')}")
PY
```

---

## 30. End-to-end “researcher audit” checklist

```bash
# 1) package integrity
python3 -m pytest tests/ -v

# 2) measured receipts
python3 scripts/verify_real_numbers_no_flub.py

# 3) compiler suite
python3 -m llm_llvm_bench.cli.main llvm run --opt-levels -O0,-O2,-O3,-Os --compiler clang \
  --out reports/llvm_benchmark_live.json

# 4) live endpoint
curl -sS https://affine.earth/language-invariant/healthz | python3 -m json.tool >/tmp/healthz.json

# 5) (optional) point a real model at affine_domain
# export OPENAI_API_KEY=… ; export OPENAI_BASE_URL=…
# python3 -m llm_llvm_bench.cli.main llm run --models … --provider openai --suites affine_domain --out reports/llm_live.json

# 6) archive
tar czf /tmp/affine-bench-receipts-$(date -u +%Y%m%dT%H%M%SZ).tgz reports/
echo "Archive ready"
```

---

## Next

- Interpret JSON fields → [Benchmarks](Benchmarks)
- Suite inventory → [Test Suites](Test-Suites)
- Q&A → [FAQ](FAQ)

---

## 31. Record a complete local LLVM evidence bundle

```bash
python3 -m llm_llvm_bench.cli.main llvm run \
  --opt-levels -O0,-O2,-O3,-Os \
  --compiler clang \
  --out reports/llvm_evidence.json

git rev-parse HEAD > reports/source_commit.txt
clang --version > reports/clang_version.txt
shasum -a 256 reports/llvm_evidence.json reports/llvm_evidence.md \
  > reports/llvm_evidence.SHA256
```

Use this when sharing a compiler result: the report alone does not identify the
source revision or compiler version.

---

## 32. Ask the public service only for liveness

```bash
curl --fail --show-error --silent \
  -D reports/healthz_headers.txt \
  https://affine.earth/language-invariant/healthz \
  -o reports/healthz_body.json

python3 -m json.tool reports/healthz_body.json
shasum -a 256 reports/healthz_headers.txt reports/healthz_body.json
```

This captures a health observation. It does not provide an LLM completion,
model inventory, or benchmark score.

---

## 33. Confirm an OpenAI-compatible target before an LLM run

```bash
export OPENAI_BASE_URL="https://your-host/v1"
export OPENAI_API_KEY="..."

curl --fail --show-error --silent \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  "$OPENAI_BASE_URL/models" \
  | tee reports/provider_models.json \
  | python3 -m json.tool
```

Save this output alongside the run report so a reader can identify the target
that accepted the request.

---

## 34. Run all built-in domain suites against a compatible model

```bash
export MODEL_ID="your-model-id"
python3 -m llm_llvm_bench.cli.main llm run \
  --models "$MODEL_ID" \
  --provider openai \
  --endpoint "$OPENAI_BASE_URL/chat/completions" \
  --api-key "$OPENAI_API_KEY" \
  --suites code,reasoning,affine_domain \
  --out reports/llm_provider_run.json
```

The code currently expects the full chat-completions URL in `--endpoint`.
Inspect the resulting JSON before citing `accuracy_pct`; it represents only
the small bundled suite and the returned responses for this run.

---

## 35. Review generated LLM answers and evaluator decisions

```bash
python3 - <<'PY'
import json
report = json.load(open("reports/llm_provider_run.json"))
for suite in report["llm_suites"]:
    print("\n##", suite["model_name"], suite["suite_name"])
    for result in suite["results"]:
        print(result["sample_id"], "PASS" if result["passed"] else "FAIL")
        print(result["generated_text"][:300].replace("\n", " "))
        if result["error_message"]:
            print("ERROR:", result["error_message"])
PY
```

This is the quickest way to catch transport failures that would otherwise
appear as low model accuracy.

---

## 36. Run one suite to isolate a provider issue

```bash
python3 -m llm_llvm_bench.cli.main llm run \
  --models "$MODEL_ID" \
  --provider openai \
  --endpoint "$OPENAI_BASE_URL/chat/completions" \
  --api-key "$OPENAI_API_KEY" \
  --suites affine_domain \
  --out reports/llm_affine_domain_only.json
```

The current `affine_domain` suite contains three prompts. Use it to debug
auth, schema, and code-extraction behavior before a broader evaluation.

---

## 37. Exercise the Anthropic provider path

```bash
export ANTHROPIC_API_KEY="..."
python3 -m llm_llvm_bench.cli.main llm run \
  --models claude-model-id \
  --provider anthropic \
  --api-key "$ANTHROPIC_API_KEY" \
  --suites code,reasoning \
  --out reports/llm_anthropic.json
```

The package calls Anthropic's Messages API directly for this provider. Retain
the model ID and generated report; do not compare timing with a different
provider unless the request conditions are documented.

---

## 38. Start and check the local dashboard

Terminal A:

```bash
python3 -m llm_llvm_bench.cli.main serve --host 127.0.0.1 --port 8888
```

Terminal B:

```bash
curl -sS http://127.0.0.1:8888/api/status | python3 -m json.tool
open http://127.0.0.1:8888
```

The status endpoint proves that the local server is listening. The dashboard
contains static display values in the current source; it is not a report
viewer.

---

## 39. Run EleutherAI lm-eval with an artifact directory

```bash
mkdir -p reports/third_party/lm_eval
git clone https://github.com/EleutherAI/lm-evaluation-harness.git \
  harnesses/lm-evaluation-harness
cd harnesses/lm-evaluation-harness
git rev-parse HEAD | tee ../../reports/third_party/lm_eval/upstream_commit.txt
python3 -m pip install -e .
cd ../..

lm_eval --model openai-chat-completions \
  --model_args "model=$MODEL_ID,base_url=$OPENAI_BASE_URL" \
  --tasks gsm8k --num_fewshot 0 --batch_size 1 \
  --output_path reports/third_party/lm_eval/gsm8k \
  2>&1 | tee reports/third_party/lm_eval/gsm8k.log
```

Check the installed `lm_eval --help` before running: upstream adapter names
and arguments evolve. Full procedure: [Third-Party Harness Reproduction](Third-Party-Harness-Reproduction).

---

## 40. Bundle a direct upstream run

```bash
find reports/third_party -type f -print0 | sort -z \
  | xargs -0 shasum -a 256 > reports/third_party/SHA256SUMS.txt
tar -czf "/tmp/affine-third-party-$(date -u +%Y%m%dT%H%M%SZ).tgz" \
  reports/third_party
```

The bundle should contain the command log, upstream commit, provider model
identity, output directory, metric JSON, and checksums. Do not replace any of
those files with manually produced receipt JSON.
- Prompts/answers → [Human-Verifiable Test Bank](Human-Verifiable-Test-Bank-and-Answers)

---

## 41. Hardest-suite preflight: validate target and create provenance bundle

Run this before any HLE, ARC-AGI, GPQA Diamond, FrontierMath, SWE-bench,
LiveCodeBench, or GAIA evaluation:

```bash
export OPENAI_BASE_URL="https://your-compatible-host/v1"
export OPENAI_API_KEY="..."
export MODEL_ID="your-model-id"
export SUITE="gpqa_diamond"  # change for the suite you are running
export RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
export OUT="reports/third_party/$SUITE/$RUN_ID"

mkdir -p "$OUT"
git rev-parse HEAD > "$OUT/affine_harness_commit.txt"
python3 --version > "$OUT/python_version.txt"
curl --fail --show-error --silent \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  "$OPENAI_BASE_URL/models" | tee "$OUT/provider_models.json"
printf 'model=%s\nendpoint=%s\nsuite=%s\nstarted=%s\n' \
  "$MODEL_ID" "$OPENAI_BASE_URL" "$SUITE" "$RUN_ID" > "$OUT/run_manifest.txt"
```

Do not continue if the endpoint probe returns HTML or another non-model JSON
payload. That is a readiness failure, not a benchmark score.

---

## 42. SWE-bench Verified evidence recipe

```bash
export SUITE="swe_bench_verified"
export RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
export OUT="reports/third_party/$SUITE/$RUN_ID"
mkdir -p "$OUT"

# Clone/install the official evaluator according to its current documentation.
# Record its exact revision before invoking the evaluator:
git -C /path/to/SWE-bench rev-parse HEAD | tee "$OUT/upstream_commit.txt"

# Run the official evaluator with your target adapter; retain all output:
# <official SWE-bench command for the pinned revision> 2>&1 | tee "$OUT/run.log"

find "$OUT" -type f -print0 | sort -z | xargs -0 shasum -a 256 > "$OUT/SHA256SUMS.txt"
```

Store generated patches and per-instance evaluator output. Until that bundle
exists, any comparison cell is **BASELINE_TABLE_ONLY**.

---

## 43. ARC-AGI and reasoning-suite evidence recipe

```bash
export SUITE="arc_agi"
export RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
export OUT="reports/third_party/$SUITE/$RUN_ID"
mkdir -p "$OUT"

# Pin the dataset/evaluator version and retain the exact predictions:
git -C /path/to/arc-evaluator rev-parse HEAD | tee "$OUT/upstream_commit.txt"
# <official ARC scorer command> 2>&1 | tee "$OUT/scorer.log"

# Copy or generate: predictions.json, task manifest, and scorer metrics JSON.
find "$OUT" -type f -print0 | sort -z | xargs -0 shasum -a 256 > "$OUT/SHA256SUMS.txt"
```

Use the same structure for HLE, GPQA Diamond, and FrontierMath: replace task
predictions with answer records, preserve the official grader output, and
retain the model/sampling manifest.

---

## 44. GAIA tool-use evidence recipe

```bash
export SUITE="gaia"
export RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
export OUT="reports/third_party/$SUITE/$RUN_ID"
mkdir -p "$OUT"

# Record the benchmark split, tool policy, final answers, and evaluator output.
printf 'tool_policy=recorded\n' > "$OUT/tool_policy.txt"
# <official GAIA evaluation command> 2>&1 | tee "$OUT/run.log"
find "$OUT" -type f -print0 | sort -z | xargs -0 shasum -a 256 > "$OUT/SHA256SUMS.txt"
```

If tool traces cannot be published, record why and preserve a reproducible
policy manifest. See [Open AGI Frameworks](Open-AGI-Frameworks) and
[Hardest Tests](Hardest-Tests).
