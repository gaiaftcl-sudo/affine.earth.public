# Affine.Earth Public Benchmark Methodology

## Scope

This repository measures two independent surfaces:

1. local LLVM compilation and execution behaviour; and
2. responses from an LLM endpoint explicitly supplied by the operator.

It also provides launchers for upstream third-party harnesses. Those launchers
run the upstream tools and preserve their output; they do not generate scores.

## Provenance rules

Every result must be classified before it is cited:

- **MEASURED**: produced by an executable command in this repository with the
  command, timestamp, configuration, and raw report available.
- **BASELINE**: historical or externally sourced data retained for comparison.
  A baseline is not evidence of a fresh run.
- **UNAVAILABLE**: a required endpoint, credential, dependency, or checkout was
  absent. No score is inferred.

The published inventory records the current state of bundled and upstream
surfaces: [BENCHMARK_INVENTORY.md](BENCHMARK_INVENTORY.md).

## Local verification

`bin/verify-rig.sh` runs the ten pytest tests and
`scripts/verify_real_numbers_no_flub.py`. The verification script compiles and
executes a C program with local `clang` at `-O0`, `-O2`, `-O3`, and `-Os`; it
also records exact-integer arithmetic timing. It makes no network request by
default.

Pass `--live` only with an explicit `AFFINE_HEALTHCHECK_URL`. A failed network
request fails the command; it is never converted into a successful response.

## LLM measurement

Live LLM runs require `AFFINE_ENDPOINT` (the full
OpenAI-compatible `/chat/completions` URL) and `AFFINE_MODEL`. The suite
selection is explicit (`affine_domain`, `code`, `reasoning`) and report output
contains the suite-level accuracy, latency, and token data returned or derived
for that run.

The report is meaningful only for the exact endpoint, model identifier,
configuration, and time recorded in its provenance sidecar. Endpoint reachability
or health checks are not model-quality measurements.

## LLVM measurement

`llm-llvm-bench llvm run` measures the bundled C microbenchmarks using the
selected compiler and optimization levels. Compile time, execution time, code
size, and IR counters depend on compiler revision, target architecture, host
load, and operating-system tooling. Runs should include the compiler version and
host metadata when compared across machines.

## Third-party harnesses

`bin/run-official-leaderboard-harnesses.sh` invokes upstream tools only after it
has been given a configured endpoint and model:

- EleutherAI `lm-evaluation-harness`;
- BigCode `bigcode-evaluation-harness`; and
- LMSYS FastChat MT-Bench.

See `config/third_party_harnesses/env.example` and
`config/third_party_harnesses/harnesses.yaml` for the Workstream A harness
configuration. Upstream versions, task revisions, sampling parameters, judge
configuration, and raw artifacts must accompany any reported result.

## Reproduction checklist

1. Record the commit SHA and Python/compiler versions.
2. Start with `./bin/verify-rig.sh`.
3. Save reports under a dated `reports/receipts_<UTCSTAMP>/` directory.
4. For live endpoints, retain the non-secret configuration and provenance JSON.
5. For upstream harnesses, retain their native output and command logs.
6. Label results **MEASURED**, **BASELINE**, or **UNAVAILABLE** in every public
   comparison.
