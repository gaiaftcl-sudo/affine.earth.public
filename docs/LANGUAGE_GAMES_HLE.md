# Language Game: Humanity's Last Exam

This is pre-submission technical doctrine for the public test repository. It
describes the `cais/hle` and CAIS-harness evaluation contract, including the
gated-dataset prerequisite. It does not claim Accuracy or Calibration.

Official sources: <https://agi.safe.ai/>, <https://github.com/centerforaisafety/hle>,
and <https://huggingface.co/datasets/cais/hle>.

**Franklin root baseline:**
[FRANKLIN_UUM8D_GAME_COMPREHENSION_SYSTEM_PROMPT.md](FRANKLIN_UUM8D_GAME_COMPREHENSION_SYSTEM_PROMPT.md).

## 1. The game

Humanity's Last Exam is an exact-answer evaluation game over difficult,
multi-domain questions. A question, its permitted context, and its response
format establish the turn. The model answers once in the evaluator's expected
format; the official judge compares that answer to the task's answer contract.

The turns are:

1. The harness loads an official question record and its modality/format.
2. The model establishes the complete question context and response contract.
3. The model generates one final answer in the prescribed answer language.
4. The harness stores the prediction with question identity and run metadata.
5. The official CAIS judge evaluates the complete prediction artifact.
6. Accuracy and calibration, if emitted by the judge, become measured results.

The win condition is an official judged result for official questions. A
plausible chain of thought, a partial subset result, or a handcrafted
comparison does not establish an HLE score.

## 2. Input, output, and state

| Element | Contract |
| --- | --- |
| Question input | Official `cais/hle` record, including prompt, metadata, expected response type, and any supported multimodal references. |
| Modalities | Exact-match strings and structured answers; some questions may require interpreting supplied visual, mathematical, scientific, or domain-specific material. |
| Context state | Question ID, complete prompt/context, modality references, answer-format requirements, model identity, prompt template, and decoding configuration. |
| Prediction state | One normalized final answer bound to the question ID; reasoning is not substituted for the final-answer field. |
| Output artifact | Harness prediction file in the official CAIS-required layout, with run metadata and judge output retained as receipts. |
| Evaluation | Official CAIS judging over the designated full dataset/run. |

The dataset is gated. Access authorization, successful parquet retrieval, and
record parsing are prerequisites to evaluation rather than evidence of a score.

## 3. Communication invariants for Affine

1. **Question identity:** every answer stays bound to the original official
   question ID and dataset revision.
2. **Complete context:** the entire question, attached modality references,
   and answer instructions survive the membrane into answer state.
3. **Answer-language fidelity:** the response is normalized only according to
   the official format; it is not converted into an explanatory substitute.
4. **Modality fidelity:** image, formula, table, or textual context must be
   represented through the same supported pathway used by the harness.
5. **Run reproducibility:** model endpoint, model identifier, prompt,
   decoding settings, dataset revision, and harness revision are recorded.
6. **Judge authority:** only the CAIS judge upgrades output into Accuracy or
   Calibration; Affine must not infer a score from model confidence.

## 4. Context-setting protocol

Before emitting an HLE answer:

1. Load the official record after authenticated dataset access is verified; do
   not replace it with a copied prompt or a partial sample.
2. Bind question ID, dataset revision, modality payload, expected answer type,
   and any evaluator normalization rules.
3. Determine what answer form the judge accepts: literal string, constrained
   choice, mathematical form, structured response, or other record-specific
   form.
4. Resolve the question using all supplied content. If a modality cannot be
   consumed through the configured model/harness path, record the capability
   gap rather than fabricate an answer state.
5. Produce one final answer in the bound format and retain it separately from
   any internal explanation.
6. Validate prediction identity and formatting before it enters the run
   artifact.

This establishes question comprehension before generation. It prevents
instruction loss, question/answer misalignment, and format drift.

## 5. Formal question-to-answer state change

For an official record `q = (id, c, m, f)`, where `c` is complete textual
context, `m` supported modality context, and `f` the answer-format contract:

```text
context(q) = (id, c, m, f, dataset_revision, run_configuration)
a = normalize_f(model(context(q)))
prediction = (id, a, run_configuration)
```

The run artifact is valid only when every prediction retains its source ID:

```text
P = { prediction(q_i) | q_i ∈ official evaluation set }
judge(P, official references) → official metrics and receipts
```

The formal answer is the normalized final prediction. A prose explanation,
confidence estimate, or transport-level HTTP success is not the answer state.

## 6. Local drift checks

| Check | Detects |
| --- | --- |
| Dataset authorization and `PAR1` parquet probe | Gated-access or download failure; this is a prerequisite failure, not a benchmark result. |
| Dataset revision/schema manifest | Changed record fields, question count, or response metadata. |
| Question-ID uniqueness and coverage validator | Dropped, duplicated, or mismatched predictions. |
| Prompt/modality capture receipt | Context truncation or missing attachments. |
| Final-answer-format validator | Answers that cannot be consumed by the official judge. |
| Model and decoding manifest | Unrecorded run configuration drift. |
| CAIS prediction and judge artifact validation | The only local-to-official bridge for Accuracy/Calibration. |

Changed parquet schema, official instruction fields, answer-format metadata, or
judge interface is **exam-spec drift**. Stable inputs with missing context,
invalid answer formatting, or wrong answers are **understanding drift**.

## 7. Affine.Earth UI language-game mapping

| UI game | HLE role |
| --- | --- |
| Linguistic membrane | Carries full question language, modality references, and response instructions into a question-bound context record. |
| Formal game | Defines question identity, answer type, normalization contract, prediction coverage, and judge-bound artifact invariants. |
| Coding game | Loads the official dataset, invokes the configured endpoint, validates prediction files, and runs the CAIS harness/judge. |

The UI can expose a question discussion, but its evaluated move is the exact
final answer bound to the official record and preserved in the prediction
artifact.

## 8. Submission gate

**No public HLE submission or score statement is permitted until local
validators are green.** The minimum green set is authorized official-data
access, revision/schema validation, full question coverage, modality/context
capture, final-answer-format validation, prediction-artifact validation, and a
successful official CAIS judge receipt. Until then, the only valid status is a
measured access or harness state, never Accuracy or Calibration.
