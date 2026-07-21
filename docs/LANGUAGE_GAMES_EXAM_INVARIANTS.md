# Language Games: Exam Invariants

This hub connects the pre-submission language-game specifications for the three
public exam tracks:

- [ARC Prize 2026 — ARC-AGI-2](LANGUAGE_GAMES_ARC_AGI_2.md)
- [ARC Prize 2026 — ARC-AGI-3](LANGUAGE_GAMES_ARC_AGI_3.md)
- [Humanity's Last Exam](LANGUAGE_GAMES_HLE.md)

These documents describe how Affine carries question context across the
linguistic membrane, formalizes the permitted answer transition, and verifies
the emitted artifact before any public action. They are not score reports.

**Franklin absolute execution baseline:**
[FRANKLIN_UUM8D_GAME_COMPREHENSION_SYSTEM_PROMPT.md](FRANKLIN_UUM8D_GAME_COMPREHENSION_SYSTEM_PROMPT.md).

**Permanent miss → reinject → closure loop:**
[EXAM_MISS_REINJECTION_LOOP.md](EXAM_MISS_REINJECTION_LOOP.md) —
`bin/run-exam-reinjection-loop.sh` (daemon-friendly). Loads ARC-2/3 + HLE fail
receipts, Franklin S1–S4/C4 repair, local mastery retest, 29-turn Aristotelian
turn log. No Kaggle submit.

## The common language game

Every exam is a controlled exchange with four roles:

```text
official question state → Affine context state → validated answer artifact → official evaluator
```

The concrete move differs by track:

| Track | Question state | Answer move | Official evaluator |
| --- | --- | --- | --- |
| ARC-AGI-2 | Training grid pairs plus held-out test grid | Two ranked output grids in `submission.json` | Exact hidden-grid match |
| ARC-AGI-3 | Interactive environment observation and trajectory | Framework-valid action sequence in `submission.parquet` | Official agent environment/evaluator |
| HLE | Official question record, format, and supported modality context | Question-bound exact final answer in CAIS prediction artifact | Official CAIS judge |

The common win condition is not an explanation or a local transport success.
It is a valid official artifact evaluated by the official evaluator.

## Invariants across all three tracks

### 1. Identity is preserved

Every answer retains the ID of the task, episode, or question that created it.
No artifact may be built from unbound outputs, reordered records, or
cross-example state.

### 2. Complete question context precedes the answer

The system consumes the whole official question contract before emission:

- ARC-AGI-2: all demonstration pairs and the test grid;
- ARC-AGI-3: the current observation, legal actions, and episode history;
- HLE: complete record, modality references, response instructions, and
  official format.

### 3. The answer is typed by the exam, not by prose

| Track | Typed answer |
| --- | --- |
| ARC-AGI-2 | Rectangular integer grids for `attempt_1` and `attempt_2` |
| ARC-AGI-3 | A legal action at each turn, then official parquet serialization |
| HLE | A normalized exact-answer field bound to the official question ID |

Natural-language reasoning may help establish state, but it never replaces the
typed answer field.

### 4. State transitions have an external authority

Affine may propose a grid transformation, an agent action, or a final answer.
It may not invent the evaluator's state transition:

- ARC-AGI-2 demonstrations and hidden labels determine grid correctness.
- ARC-AGI-3 environment responses determine the next episode state.
- HLE's CAIS judge determines metrics.

### 5. Local evidence is labeled locally

Schema validation, demonstration replay, starter verification, and CAIS
artifact checks are local evidence. They establish readiness, not a public
score. Only platform or official judge receipts establish public results.

### 6. Serialization is a semantic boundary

The endpoint payload is not an incidental export:

- `submission.json` is part of the ARC-AGI-2 answer.
- `submission.parquet` is part of the ARC-AGI-3 trajectory answer.
- the CAIS prediction artifact is part of the HLE answer.

The serializer must therefore be validated against the same state that was
understood and solved.

## Context-to-answer protocol

Apply this sequence to every task, episode, or question:

1. **Bind:** capture official identity, revision/version, complete context, and
   answer contract.
2. **Parse:** convert the question into track-native typed state.
3. **Constrain:** enumerate only moves legal under that state and contract.
4. **Validate locally:** replay demonstrations, validate actions, or check
   answer format and coverage as relevant.
5. **Serialize:** emit through the official adapter with provenance retained.
6. **Gate:** require the relevant local validators and preflight receipt.
7. **Evaluate officially:** treat externally returned platform/judge evidence
   as the sole source of public score status.

## Drift taxonomy

| Drift kind | Meaning | Response |
| --- | --- | --- |
| Exam-spec drift | Official schema, starter API, dataset revision, action contract, or judge contract changed. | Update the parser/adapter/validator, rerun preflight, and retain the new manifest. |
| Understanding drift | The official contract is stable, but the inferred rule, action, context, or answer is invalid. | Correct the task-native reasoning and rerun local validation. |
| Serialization drift | The validated internal state differs from the emitted JSON/parquet/prediction artifact. | Repair the adapter and prove state-to-artifact equality. |
| Evidence drift | A local result is presented as a public score or lacks a receipt. | Restore the correct label and retain the source artifact. |

## Affine.Earth UI mapping

The same UI language-game stack applies across exams:

| Layer | Responsibility |
| --- | --- |
| Linguistic membrane | Preserve full question context and make its answer language explicit. |
| Formal | Bind identity, type state, legal transitions, and acceptance conditions. |
| Coding | Invoke official adapters/harnesses, validate artifacts, and retain receipts. |

This prevents a conversational response from drifting away from the
machine-evaluated answer state.

## Hard public-submission gate

**No public Kaggle or HLE submission occurs until the relevant local validators
are green and a preflight receipt exists.** The required validators are
track-specific and are defined in the linked pages. Green local validation is a
readiness condition, not an invented score; every public result must cite the
corresponding official receipt.

## Format from top scores

Artifact contracts and FoT contrast (AGI-3 **0.12** vs LB ~1.86):
[KAGGLE_ARC_TOP_SCORE_FORMATS.md](KAGGLE_ARC_TOP_SCORE_FORMATS.md).
