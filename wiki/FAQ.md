# FAQ / Q&A

![Affine.Earth live language-game](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/hero-language-game.png)

**Story spine:** [Home](Home) (UI all-tests hero) · [In action](In-Action) · [Results & Scores](Results-And-Scores) · [AGI agent execution](AGI-Agent-Execution).  
**Signup / login video once:** [Create account](Create-Account-Signup) (not embedded elsewhere).

Detailed questions and answers about Affine.Earth OS and this public evidence wiki.

---

## Project basics

### Q. What repository is this wiki for?

**A.** [`https://github.com/gaiaftcl-sudo/affine.earth.public`](https://github.com/gaiaftcl-sudo/affine.earth.public). The executable harness lives primarily under `llm-llvm-benchmark-suite/`. The wiki git remote is `https://github.com/gaiaftcl-sudo/affine.earth.public.wiki.git`.

### Q. Is this a Bitcoin miner or mainnet simulation project?

**A.** No. This public repo/wiki documents an **LLM + LLVM benchmark harness** and Affine.Earth endpoint probes. It does not claim mining rewards, wallet balances, or mainnet block submission. Ignore any unrelated mining narratives when reading these pages.

### Q. What is Affine.Earth in this context?

**A.** A live service with at least:

- Health: `https://affine.earth/language-invariant/healthz` (measured HTTP 200)
- Language-game UI + **Sovereign entry** (wallet-based account): see [Create Account / Signup](Create-Account-Signup)
- OpenAI-compatible style `/v1` is documented for harness routing, but measured 2026-07-20 `https://affine.earth/v1/models` returned **HTML**, not models JSON

The suite measures and documents that surface; it does not replace reading the live response yourself.

### Q. How do I create a new Affine.Earth user?

**A.** There is no email/password register form. Correct UI path:

1. `https://affine.earth` → **New wallet**
2. Check the **consent** checkbox
3. **Use my location**
4. **Create wallet + QFOT** → wait until the **app opens** (~8s measured)
5. **Export private key** from Docs / Profile

Then open **Games** → **Linguistic membrane (chat)** to see test Q&A in the UI (`#messageList` + clarifying-answer fields). Full steps: [Create Account / Signup](Create-Account-Signup). Do this **before** CLI harness claims.

### Q. Where do test questions and answers appear in the product UI?

**A.** After the app opens: **Games** (`#gamesBtn`) → pick **Linguistic membrane (chat)** (or Formal manifold / Coding). Questions show as Franklin bubbles in `#messageList`; you answer via “Message Franklin…” and the clarifying-answer / “Anything else?” verify fields. Package CLI test banks are separate — see [Human-Verifiable Test Bank](Human-Verifiable-Test-Bank-and-Answers).

### Q. Does Create wallet always credit genesis QFOT on the mesh?

**A.** **FIXED** (GaiaFTCL SHA `cf3cd8249`, 9-cell deploy). FoT + UI E2E re-verify (2026-07-20 evening): `POST /language-invariant/economics-onboard` is **live** on the language-inject sidecar. Measured: `status: PROVEN_ECONOMICS_ONBOARD`, `genesis_credited: 100/1`, `GET …/qfot-balance?address=…` returns **PROVEN** `100/1`. After Create wallet + QFOT, Profile shows **BALANCE STATUS: PROVEN** and **QFOT BALANCE: 100/1** (not BLOCKED / 0/1).

**Historical note:** Earlier the same day the sidecar returned **HTTP 404** on `economics-onboard`, so the app could open while genesis credit failed (Profile **BLOCKED / 0/1**). That is no longer current.

### Q. What Python version is required?

**A.** Python **≥ 3.9** per `pyproject.toml`. Verified with 3.9.6.

---

## Installation & tooling

### Q. How do I install the package?

**A.**

```bash
cd llm-llvm-benchmark-suite
pip install -e .
```

Dependencies: `requests`, `click`, `pytest` (see `pyproject.toml` / `requirements.txt`).

### Q. Do I need Clang?

**A.** Yes for LLVM suites, `tests/test_llvm.py`, and `scripts/verify_real_numbers_no_flub.py`. LLM-only mock runs do not require Clang.

### Q. How many pytest tests should I expect?

**A.** As of 2026-07-20 the tree collects **10** pytest tests (`test_core` 3 + `test_forks` 2 + `test_llm` 3 + `test_llvm` 2). Confirmed with `pytest --collect-only` → `10 tests collected` and `10 passed`. Prefer that over any older “8 passed” wording in archived copies.

### Q. Can I run without network?

**A.** Yes for:

- `pytest` (except if something unexpectedly hits network; current tests are local)
- `llm run --provider mock`
- `llvm run` (local clang)

Network required for live healthz / Affine `/v1` / remote LLM providers. The verify script **does** probe healthz.

---

## Test suites

### Q. What LLM suites exist?

**A.** `code`, `reasoning`, `affine_domain` in `llm_llvm_bench/llm/suites.py`. Details: [Test Suites](Test-Suites).

### Q. What does the mock provider prove?

**A.** That CLI wiring, provider selection, suite iteration, and report writers work. Measured mock accuracy was **0%** — that is not a model quality claim.

### Q. How is “pass” decided for code samples?

**A.** `LLMEvaluator.evaluate_code` executes model-extracted Python against `test_cases` asserts. All asserts must succeed.

### Q. Does a functional pass mean constant-time security?

**A.** No. Early-exit compares can still pass functional asserts. The human audit criteria are in [Human-Verifiable Test Bank](Human-Verifiable-Test-Bank-and-Answers): loop must process all bytes without data-dependent early return.

### Q. What LLVM programs are benchmarked?

**A.** Two C programs: `llvm_micro_matrix_mul` (200×200 matmul) and `llvm_codesize_sort` (bubble sort). See `llm_llvm_bench/llvm/benchmarks.py`.

### Q. Why is `.text` often 16,384 bytes on Apple Silicon?

**A.** That is what `size` reported for these binaries in measured runs (page/section alignment can make small programs share similar reported sizes). Always trust the receipt from **your** machine.

---

## Benchmarks & results interpretation

### Q. Where are the authoritative measured numbers?

**A.** Prefer dated files under `reports/`, especially:

- `real_verification_proof.json`
- `llvm_benchmark_live.json`

Wiki tables should cite those or a re-run. See [Benchmarks](Benchmarks).

### Q. What does `float_drift: 0.0` mean?

**A.** The verification path performed 10,000 exact rational additions using integer numerator/denominator arithmetic and recorded zero drift versus that exact path. It is **not** a claim that every IEEE 754 operation on the host is associative.

### Q. Why do healthz latencies jump between 120ms and 280ms?

**A.** Network path, TLS, DNS, and server load. Use healthz for liveness; do not treat single RTT samples as substrate kernel latency.

### Q. What does `proven_status: REAL_NUMBERS_VERIFIED_NO_FLUB` mean?

**A.** The verify script completed its Clang + rational + live probe checks and stamped the JSON. Re-run the script to refresh the stamp.

### Q. Are all 100% scores from full upstream harness runs?

**A.** **Not automatically.** Distinguish:

1. **Locally measured** Clang/rational/pytest results (this session re-ran them).
2. **Baseline comparative tables** in `expanded_frontier_baselines.py` / leaderboard pages (published/model-card style aggregates for frontier models; Affine columns are substrate claims in those tables).
3. **Receipt JSON** for BigCode/MT-Bench written by `bin/run-official-leaderboard-harnesses.sh` — inspect the script: some sections emit structured JSON via shell heredoc. For independent third-party evidence, run the upstream CLIs from [BigCode](BigCode-bigcode-evaluation-harness) / [FastChat](LMSYS-FastChat-MT-Bench) / [EleutherAI](EleutherAI-lm-evaluation-harness) and overwrite receipts with harness-native output.

### Q. How should I cite a number in a paper or audit?

**A.** Include: command, host OS/CPU, clang version, UTC timestamp from the JSON, and the file hash or commit SHA of `affine.earth.public`. Example:

> “On 2026-07-20 UTC, `verify_real_numbers_no_flub.py` reported `float_drift=0.0` and clang `-O3` exec 67.76ms (`reports/real_verification_proof.json`).”

### Q. Why is Affine shown as 100% on SWE-bench in the leaderboard?

**A.** That figure appears in the comparative baseline table (`expanded_frontier_baselines.py` / wiki Expanded Coding page) as an Affine kernel claim relative to published frontier scores. This wiki does **not** currently attach a full SWE-bench Verified run log under `reports/` for all 500 issues. Treat it as a **baseline table entry**, and require steward-supplied harness logs before treating it as an independent SWE-bench reproduction.

### Q. What about HumanEval Pass@1 = 1.0 in `affine-bigcode-results.json`?

**A.** The file on disk contains that score. Confirm production path (wrapper receipt vs BigCode `main.py` metrics export) before citing as an upstream-harness reproduction.

### Q. How do I read IR instruction counts?

**A.** Lower load/store/branch counts after `-O2`/`-O3` usually indicate successful optimization on the matmul kernel. Counts are descriptive, not a single “score.”

### Q. Can timings be compared across machines?

**A.** Only with caveats (CPU, thermal, clang version, SIP, background load). Prefer relative rankings **within one run**.

---

## Harnesses & submissions

### Q. Which upstream harnesses are vendored?

**A.** Under `harnesses/`: EleutherAI `lm-evaluation-harness`, BigCode `bigcode-evaluation-harness`, LMSYS `FastChat`.

### Q. What API key does the public verifier use?

**A.** Measured bootstrap for the Affine.Earth OS membrane (**2026-07-24**): `AFFINE_BASE_URL=https://affine.earth`, `AFFINE_API_KEY=uum8d-hle-verifier` (wire aliases `OPENAI_BASE_URL=https://affine.earth/v1`, `OPENAI_API_KEY` — NOT api.openai.com). `GET /v1/models` returned HTTP 200 JSON (`gaiaftcl-os`, `affine-earth-os-mcp`, `franklin-membrane`, `franklin-membrane-exam`); `POST /v1/chat/completions` returned HTTP 200 (`franklin-membrane`). Receipt: `reports/wiki_membrane_probe_20260724/receipt.json`. Prefer `developer-suite/examples/03_openai_models_and_chat.py` / `docs/OPENAI_V1.md`. Signup does **not** mint keys in the UI.

### Q. What is the local interceptor?

**A.** `llm_llvm_bench/server/affine_v1_interceptor.py` — OpenAI-compatible wire-frame server used by `run-official-leaderboard-harnesses.sh` on `127.0.0.1:8000`.

### Q. Where are global leaderboard submission notes?

**A.** Repo file `docs/GLOBAL_LEADERBOARD_SUBMISSIONS.md` and wiki harness pages. Submission to Hugging Face / BigCode / LMSYS is a separate process from regenerating local receipts.

### Q. How do I publish wiki updates?

**A.** Maintainers: `python3 scripts/publish_public_wiki.py` or push to `affine.earth.public.wiki.git` on branch `master`.

---

## CLI & dashboard

### Q. What are the top-level CLI commands?

**A.** `llm`, `llvm`, `serve` (`python3 -m llm_llvm_bench.cli.main --help`).

### Q. Where does `serve` listen?

**A.** Default `http://127.0.0.1:8888`.

### Q. Why do I see a RuntimeWarning about `llm_llvm_bench.cli.main` and `runpy`?

**A.** Harmless warning when invoking the module as `__main__` after package import on some Python 3.9 builds. Prefer the `llm-llvm-bench` console script after install if you want to avoid it.

---

## Troubleshooting

### Q. `clang` not found

**A.** Install Xcode CLT (`xcode-select --install`) or ensure `clang` is on `PATH`. LLVM tests will fail without it.

### Q. Healthz fails / times out

**A.** Check network, DNS, TLS interception, and that `https://affine.earth` is reachable from your host. Local pytest/llvm can still pass offline.

### Q. SSL / urllib3 LibreSSL warning

**A.** Common on macOS system Python. It is a warning, not a test failure, in measured runs.

### Q. Editable install does not expose `llm-llvm-bench`

**A.** Ensure `pip install -e .` succeeded and your `PATH` includes the user/base scripts directory. Fallback: `python3 -m llm_llvm_bench.cli.main …`.

### Q. BigCode `allow_code_execution` scares me

**A.** Upstream BigCode executes model-generated code by design for Pass@k. Run in a sandbox/VM if you do not trust completions.

### Q. Mock accuracy is 0% — is the suite broken?

**A.** No. Mock is for plumbing. Use a real provider for accuracy.

### Q. Reports directory empty

**A.** You have not run generators yet. Start with `verify_real_numbers_no_flub.py` or `./bin/run-full-benchmark.sh`.

---

## Methodology & honesty

### Q. What does “un-flubbed / un-mocked” mean in this suite?

**A.** Local verification uses real `clang`, real process execution, exact rational integer math, and a live HTTP probe — not fabricated timing constants inside those scripts. It does **not** mean every comparative leaderboard cell is a freshly executed third-party harness on every frontier model.

### Q. Where is the human-auditable prompt bank?

**A.** [Human-Verifiable Test Bank and Answers](Human-Verifiable-Test-Bank-and-Answers).

### Q. Where is the step-by-step reproduction guide?

**A.** [Un-Mocked Verification Methodology and Instructions](Un-Mocked-Verification-Methodology-and-Instructions) and [Getting Started](Getting-Started).

### Q. What gaps still need steward input?

**A.** See the steward gap list on [Home](Home) / maintainers notes:

1. Attach full upstream harness logs for HumanEval/MBPP/MMLU/GSM8k/MT-Bench if claiming third-party reproduction.
2. Attach SWE-bench / LiveCodeBench / ARC-AGI raw run artifacts if claiming those Pass rates as measured (not baseline-table) results.
3. Sync main-repo README / `docs/METHODOLOGY.md` (already corrected locally to “10 passed”) and push when ready.
4. Optionally change `run-official-leaderboard-harnesses.sh` to invoke upstream CLIs only (no heredoc receipts).

### Q. Does the local `/v1` interceptor contact Affine.Earth?

**A.** No. `llm_llvm_bench/server/affine_v1_interceptor.py` generates
responses in-process from prompt patterns. It exists to exercise a request/
response shape locally. Its responses and any files produced through it must
not be presented as live Affine.Earth results or upstream-harness metrics.

### Q. Can I use `run-official-leaderboard-harnesses.sh` for a third-party score?

**A.** No. The current shell wrapper invokes the live-domain report script for
its Eleuther step but writes BigCode and MT-Bench JSON through shell heredocs.
It is useful for showing expected report locations, not for producing
harness-native evidence. Use [Third-Party Harness Reproduction](Third-Party-Harness-Reproduction).

### Q. Does `healthz` prove an LLM model endpoint works?

**A.** No. It proves one HTTP health request completed. Validate
`$OPENAI_BASE_URL/models` and a real completion request separately before
running an OpenAI-compatible harness.

### Q. Is the dashboard populated from `reports/`?

**A.** Not currently. `llm_llvm_bench/web/server.py` embeds static charts and
tables. The JSON/Markdown output generated by the CLI is the report source;
dashboard report loading requires code work.

### Q. Why does `llm --help` mention `tool_use`?

**A.** The Click option default/help text is stale. The suite registry contains
`code`, `reasoning`, and `affine_domain`. An unrecognized suite name currently
falls back to `affine_domain`, so pass explicit valid names.

### Q. What must be present before a third-party result is published?

**A.** Preserve the upstream revision, installed dependency set, exact command
(without secrets), raw stdout/stderr, model identifier, generated answers when
the harness creates them, metric JSON, and checksums. A score copied into a
table without those artifacts is not independently reproducible.

### Q. What work is needed before the repository can automate official-harness claims?

**A.** Replace generated receipt writers with upstream CLI calls, pin upstream
dependencies, connect a verified live API target or adapter, retain
harness-native logs/artifacts, and make the dashboard consume reports rather
than static values. These are code changes, not documentation changes.

---

## Hardest tests and AGI validation

### Q. Where is the map of the hardest public evaluations?

**A.** [Hardest Tests](Hardest-Tests) covers Humanity's Last Exam, ARC-AGI,
GPQA Diamond, FrontierMath, SWE-bench Verified, LiveCodeBench, and GAIA. It
states what each one exercises and the evidence needed to call a result
**MEASURED**.

### Q. Does this wiki report an Affine score for Humanity's Last Exam?

**A.** No measured Affine HLE artifact bundle is published here. The page
documents a **RUNNABLE** evidence path and does not invent a pass rate.

### Q. What makes ARC-AGI different from ordinary question answering?

**A.** ARC-AGI presents a few input/output grids and asks for the output of a
new grid. The challenge is selecting and transferring a latent transformation,
not recalling a fact. Existing Affine comparison entries are
**BASELINE_TABLE_ONLY** until official scorer artifacts are preserved.

### Q. What does GPQA Diamond test?

**A.** It targets graduate-level questions built to resist straightforward web
lookup. A credible run requires the exact split, model/sampling configuration,
answer records, and grader output.

### Q. Can FrontierMath be called “proved” by a model answer?

**A.** No. A benchmark answer and a formal mathematical proof are different
artifacts. Record the official evaluation result; attach a proof-verification
artifact separately when one exists.

### Q. Why is SWE-bench harder than a unit-test example?

**A.** It requires locating a real issue in a repository, producing a patch in
the target environment, and passing the benchmark evaluator’s tests. The
patches, container provenance, and evaluator logs are part of the result.

### Q. What does LiveCodeBench add beyond HumanEval?

**A.** It uses time-aware contest problems intended to reduce training-data
contamination. Preserve the benchmark release/date cutoff and task IDs with
the execution logs.

### Q. What does GAIA test?

**A.** GAIA tests multi-step, tool-using tasks whose final answers can be
checked. A result needs its tool policy and, where permitted, tool traces as
well as final-answer grading.

### Q. What does “AGI framework” mean on this wiki?

**A.** It is an evidence framework across expert reasoning, abstraction,
software construction, tool use, and deterministic execution—not a claim that
one benchmark or one local receipt establishes general intelligence. See
[Open AGI Frameworks](Open-AGI-Frameworks).

### Q. Can a live health endpoint validate a benchmark run?

**A.** No. Healthz establishes liveness for one HTTP request. A benchmark run
also needs a model endpoint, model identity, upstream command, raw output, and
metric artifact.

### Q. Is `/v1` ready to receive a third-party harness today?

**A.** Treat it as ready only after the intended URL returns valid
OpenAI-compatible `/models` JSON and a real completion response using the
credential supplied for the run. The recorded 2026-07-20 observation returned
HTML at `/v1/models`; preserve a fresh probe before claiming readiness.

### Q. Why does account signup matter to benchmark provenance?

**A.** It establishes the public Sovereign entry path used to create an
evaluation identity. It does not itself issue a benchmark API credential or
prove model access. Screenshots and steps are on
[Create Account / Signup](Create-Account-Signup).

### Q. Should I publish a wallet private key with a benchmark artifact?

**A.** No. Preserve a public account/provenance reference where appropriate,
but never include private keys, session cookies, API keys, or secret endpoint
credentials in logs, reports, or wiki pages.

### Q. What is the minimum citation for a measured hard-suite result?

**A.** Include suite/version, upstream commit, model identifier, sampling
settings, exact command, UTC timestamps, metric JSON, raw log path, and
checksums. State the status label in the sentence or table caption.

### Q. May I cite a baseline table as an Affine benchmark measurement?

**A.** No. Cite it as **BASELINE_TABLE_ONLY**, name the source table, and
avoid wording that says the repository executed the suite.

### Q. What is a failure result worth retaining?

**A.** Retain transport errors, authentication failures, malformed API
responses, patches that fail tests, task-level scorer failures, and timeout
metadata. Failure artifacts identify whether the issue is endpoint readiness,
harness wiring, or model behavior.

### Q. How do LLVM and rational receipts relate to AGI tests?

**A.** They validate deterministic execution and report provenance for the
local rig. They do not substitute for HLE, ARC-AGI, GPQA, FrontierMath,
SWE-bench, LiveCodeBench, or GAIA scores.

### Q. What does the interceptor prove?

**A.** It proves local request/response contract handling. It does not contact
Affine.Earth or validate a live model; never use it as a source of hard-suite
metrics.

### Q. How do I reproduce a suite after `/v1` is available?

**A.** Follow [Hardest Tests](Hardest-Tests) for the evidence protocol, then
use [Third-Party Harness Reproduction](Third-Party-Harness-Reproduction) for
the upstream setup. Archive the run under `reports/third_party/<suite>/`.

### Q. What changes a suite from RUNNABLE to MEASURED?

**A.** A complete, dated, check-summed bundle produced by the upstream
evaluator: revision, command, model manifest, raw output, metrics, and
reproduction environment. A manually typed result table does not change the
status.

---

## Quick links

| Need | Page |
|:---|:---|
| Install | [Getting Started](Getting-Started) |
| Suite list | [Test Suites](Test-Suites) |
| Read JSON | [Benchmarks](Benchmarks) |
| Recipes | [Examples / Cookbook](Examples-Cookbook) |
| Leaderboard | [Live Leaderboard](Live-Leaderboard) |
