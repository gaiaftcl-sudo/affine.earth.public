# Language Games — Humanity's Last Exam

Pre-submission specification for [Humanity's Last Exam](https://agi.safe.ai/),
the [CAIS evaluator](https://github.com/centerforaisafety/hle), and gated
[`cais/hle`](https://huggingface.co/datasets/cais/hle). This page does not
claim Accuracy or Calibration.

Canonical doctrine: [`docs/LANGUAGE_GAMES_HLE.md`](../docs/LANGUAGE_GAMES_HLE.md)
· shared invariants: [Exam language-game invariants](Language-Games-Exam-Invariants)
· live harness record: [Humanity’s Last Exam — live](Humanitys-Last-Exam-Live)
· Franklin root baseline: [UUM-8D game comprehension](../docs/FRANKLIN_UUM8D_GAME_COMPREHENSION_SYSTEM_PROMPT.md).

## 1. Game, moves, and win condition

HLE is an exact-answer game over official, multi-domain question records. The
harness loads one question and its answer contract; the model consumes its
complete context and supported modality payload, emits one normalized final
answer, and the CAIS judge evaluates the complete prediction artifact.

**Win condition (steward):** evaluable OpenAI-compatible endpoint + harness
reproducibility + email package to evaluators (`agibenchmark@safe.ai`,
`seal@scale.com`) — not Kaggle auto-submit. Official Accuracy/Calibration still
come only from the CAIS judge after an authorized rerun. Scaffold:
`reports/hle_eval_email_package/`.

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

UI captures are interaction evidence for context-setting → answer-state change.
They are not CAIS judge output. Signup/login walkthrough video is **only** on
[Create account](Create-Account-Signup).

![HLE access gate](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-access-gate.png)

![HLE games catalog](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-games-catalog.png)

| Layer | Still | Answer / state |
| --- | --- | --- |
| Linguistic membrane | ![still](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-linguistic_membrane.png) | ![answer](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-linguistic_membrane-answer.png) |
| Formal manifold | ![still](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-formal_manifold.png) | ![answer](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-formal_manifold-answer.png) |
| Coding | ![still](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-coding.png) | ![answer](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-coding-answer.png) |
| Motion | ![gif](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-context-to-answer.gif) | [mp4](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/exam-ui-hle-context-to-answer.mp4) |

Capture: `python3 scripts/capture_hle_exam_ui.py --record-video`. Live embeds also on
[Humanity’s Last Exam — live](Humanitys-Last-Exam-Live).

## 8. Evaluation gate (email — not Kaggle)

**No HLE Kaggle / auto-submit.** Public path = email evaluators an evaluable
OpenAI-compatible system + harness config (`reports/hle_eval_email_package/`).
No Accuracy/Calibration claim until the official CAIS judge emits them. Local
`reports/hle_official_*` artifacts are corroboration only.

## 9. Local ownership drills (pre-`cais/hle`)

While classic `HF_TOKEN` is absent or parquet resolve returns 401, this workspace
still owns the language-game surface via synthetic fixtures that mirror HLE move
types. Local evidence is labeled local (shared invariant 5).

```bash
export OPENAI_BASE_URL="http://127.0.0.1:8080/v1"
export AFFINE_API_KEY="uum8d-hle-verifier"
export OPENAI_API_KEY="$AFFINE_API_KEY"  # wire → Affine.Earth OS
./bin/run-local-hle-mastery.sh
```

| Fixture move | Answer contract |
| --- | --- |
| MCQ | option letter only |
| Exact match | exact token only |
| Multimodal stub | exact token; modality recorded as unsupported text adapter |
| Boolean | literal `True` or `False` token |
| Numeric exact | integer token |
| Mathematical expression | normalized fraction token |
| Unit-bearing exact | exact converted numeric token |
| Short answer | exact entity-name token |
| Ordered sequence | comma-delimited exact sequence |
| Set-membership MCQ | option letter only |
| Formula exact | integer / reduced-form token |
| Boolean (yes/no) | literal `True` or `False` token |
| Percentage exact | integer token |
| Base conversion | integer token |
| Roman numeral | Arabic digit token |
| Multi-hop exact | integer token after chained facts |
| Code token | language literal token |
| Inequality boolean | `True` / `False` |
| Set cardinality | integer token |
| Temporal exact | integer day count |
| Matrix shape | integer entry count |
| Logic MCQ | option letter |
| S4 multi-turn exact | integer after S1–S4 framing |
| Scientific notation | integer token |
| Permutation exact | integer token |
| Acronym exact | exact expansion phrase |

Receipts land in `reports/hle_local_<UTC>/` (example:
`reports/hle_local_20260721T104720Z/`):

- `receipt.json` — endpoint/model manifest, per-question identity/format gates,
  initial and post-reinjection local match ratios, and
  `official_hle_accuracy: null`
- `language-game-turns.jsonl` — OPEN → CONTEXT → ANSWER → GATE turns
- local misses append REINJECT → CONTEXT → ANSWER → GATE turns. The fixture
  gate supplies the corrected local C4 answer, Franklin re-reads the original
  contract, and the second answer is independently checked.

Measured continuous local drill on loopback `qwen/qwen3.6-35b-a3b`
(`reports/hle_local_continuous_20260721T133500Z/receipt.json`, fixture set v2,
12 items) was GREEN after reinjection. Fixture grammar expanded to **v3 (≥24
items)** covering percentage, base conversion, Roman, multi-hop, code token,
inequality, set cardinality, temporal, matrix shape, logic MCQ, S4 multi-turn,
scientific notation, permutation, and acronym contracts.

Latest measured v3 receipt path (when present):
`reports/hle_local_continuous_v3_*/receipt.json`.

| Metric | Prior v2 | Official? |
| --- | --- | --- |
| after-reinjection local ratio | 12/12 = 1.0 | no |
| `official_hle_accuracy` | `null` | — |
| `hf_token_status` | `absent` | — |
| `official_claim_permitted` | `false` | — |

Local drills remaining GREEN is **not** CAIS Accuracy.

### Official gate (2026-07-21)

Dataset Agree/permissions on [`cais/hle`](https://huggingface.co/datasets/cais/hle)
were granted, but this host process still cannot authenticate:

- `printenv HF_TOKEN` / `HUGGING_FACE_HUB_TOKEN` → absent
- `~/.cache/huggingface/token` → **does not exist**
- `hf auth whoami` → `Not logged in`
- `load_dataset("cais/hle")` → `DatasetNotFoundError: Dataset 'cais/hle' is a gated dataset on the Hub. You must be authenticated to access it.`

Receipt: `reports/hle_official_20260721T140000Z/dataset_access.receipt.json`.
`official_hle_accuracy` remains **null**. No Keychain access attempted.


Re-run auth wait (polls env + `~/.cache/huggingface/token`, never prints secrets):

```bash
./bin/watch-hle-hf-auth.sh
# notes: docs/HLE_AUTH_WAIT.md
```

**Steward one-liner (process env only):**

```bash
hf auth login
# or: export HF_TOKEN='hf_…'
harnesses/hle/hle_eval/.venv/bin/python -c "from datasets import load_dataset; ds=load_dataset('cais/hle'); print({k:len(ds[k]) for k in ds})"
HLE_RUN_JUDGE=1 ./bin/run-open-agi-harnesses.sh --harness hle
```

Hard rules:

- No Keychain / `security` CLI.
- `HF_TOKEN` is read from the process environment only when present; local drills
  do not require it and do not use it.
- Never present local fixture match ratios as Accuracy, Calibration, or a
  leaderboard claim.
- `initial_local_fixture_match_ratio` and
  `local_fixture_match_ratio_after_reinjection` remain local drill evidence;
  neither is official Accuracy.
- Official CAIS predict+judge remains the only path that may fill
  `official_hle_accuracy`.
