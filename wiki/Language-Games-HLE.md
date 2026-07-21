# Language Games — Humanity's Last Exam

Pre-submission specification for [Humanity's Last Exam](https://agi.safe.ai/),
the [CAIS evaluator](https://github.com/centerforaisafety/hle), and gated
[`cais/hle`](https://huggingface.co/datasets/cais/hle). This page does not
claim Accuracy or Calibration.

## 1. Game, moves, and win condition

HLE is an exact-answer game over official, multi-domain question records. The
harness loads one question and its answer contract; the model consumes its
complete context and supported modality payload, emits one normalized final
answer, and the CAIS judge evaluates the complete prediction artifact. The win
condition is the official judge's result, never a plausible explanation or
partial sample run.

## 2. Input/output state

- Input: official question record, prompt/context, expected response type, and
  supported multimodal references.
- State: question ID, dataset revision, complete context, modality payload,
  response format, model/prompt/decoding configuration.
- Output: one normalized final answer per official ID in the CAIS prediction
  artifact.
- Evaluation: official CAIS judging over the designated run.

Dataset authorization and successful parquet retrieval are prerequisites; they
are not a score.

## 3. Affine communication invariants

The membrane preserves official question identity, the full question and
instructions, modality fidelity, expected answer language, and run
configuration. A final-answer field remains separate from reasoning. Only the
CAIS judge may turn predictions into Accuracy or Calibration.

## 4. Context-setting protocol

1. Verify authorized official-dataset access and load the actual record.
2. Bind ID, revision, all text and modality references, and the answer-format
   contract.
3. Determine the judge-accepted answer form before generation.
4. Resolve using all supplied context; record any unsupported modality gap
   rather than inventing an answer state.
5. Emit exactly one normalized final answer and validate its ID and format.

## 5. Formal state transition

For `q = (id, c, m, f)` with textual context `c`, modality `m`, and answer
contract `f`:

```text
context(q) = (id, c, m, f, dataset_revision, run_configuration)
a = normalize_f(model(context(q)))
prediction = (id, a, run_configuration)
```

The official transition is:

```text
full prediction artifact → CAIS judge → metrics and receipts
```

An HTTP success, explanation, or confidence estimate is not the answer state.

## 6. Local drift checks

| Check | Distinguishes |
| --- | --- |
| Authorization plus `PAR1` probe | Access prerequisite failure |
| Dataset revision/schema manifest | Exam-spec change |
| ID coverage/uniqueness validator | Prediction misbinding |
| Prompt/modality receipt | Missing or truncated question context |
| Answer-format validator | Judge-incompatible output |
| Model/decoding manifest | Run configuration drift |
| CAIS artifact and judge receipt | Only bridge to official metrics |

Schema, format, or judge-interface changes are exam-spec drift. Stable inputs
with missing context or invalid answers are understanding drift.

## 7. Affine UI mapping

- **Linguistic membrane:** preserves question language, modality references,
  and output instructions.
- **Formal:** binds identity, answer type, coverage, and judge constraints.
- **Coding:** loads the dataset, invokes the configured endpoint, and produces
  a validated CAIS artifact.

## 8. Public-submission gate

**No public HLE submission or score statement until authorized data access,
schema validation, complete coverage, context capture, answer-format checks,
artifact validation, and a successful official CAIS judge receipt are green.**
# Language games for Humanity’s Last Exam

This workspace owns a local-first language-game layer before it has authorization to retrieve `cais/hle`. It operates against the OpenAI-compatible loopback at `http://127.0.0.1:8080/v1` and records every response as a receipt.

## Local drill contract

`bin/run-local-hle-mastery.sh` sends three transparent, locally authored fixtures:

- MCQ: answer convention is the option letter.
- Exact match: answer convention is the requested token.
- Multimodal stub: a text-only adapter description, explicitly marked as a stub rather than an image evaluation.

Every turn directs the model to set the answer convention in `context` before returning `answer`. The receipt includes both fields, raw model output, response timing, endpoint model list, and a fixture-only match count.

```bash
export OPENAI_BASE_URL="http://127.0.0.1:8080/v1"
export OPENAI_API_KEY="uum8d-hle-verifier"
./bin/run-local-hle-mastery.sh
```

The generated `reports/hle_local_<UTC timestamp>/receipt.json` is not a CAIS artifact. Its `synthetic_fixture_accuracy` is deliberately distinct from `official_hle_accuracy`, which remains `null`.

## Local ownership gate

The local drills are always runnable without Hugging Face credentials. They do not read macOS Keychain, call `security`, or use cached Hub credentials. A classic `HF_TOKEN` supplied through the process environment is only used by the official upstream path after the steward has accepted the `cais/hle` dataset terms.

## Official HLE gate

The public/CAIS path is separate:

1. Set a classic `HF_TOKEN` in the harness shell after access has been granted.
2. Run an upstream prediction smoke slice without judging.
3. Run a larger prediction slice without judging when its receipt is complete.
4. Run the full 2,500-question upstream prediction and judge flow.
5. Retain upstream prediction and judge JSON before making any score or leaderboard claim.

The judge divides by the entire test set, so a smoke subset must never be presented as official HLE accuracy. See [Humanity’s Last Exam — live harness record](Humanitys-Last-Exam-Live).

## UI proof boundary

The Affine Earth captures show language-game context-setting and answer-state transitions. They are interaction evidence, not evaluator output, prediction provenance, or a score.
