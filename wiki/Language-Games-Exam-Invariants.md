# Language Games — Exam Invariants

This is the pre-submission hub for the three public exam tracks:

- [ARC-AGI-2](Language-Games-ARC-AGI-2) — static grid transformation with
  `attempt_1` / `attempt_2`.
- [ARC-AGI-3](Language-Games-ARC-AGI-3) — interactive agent trajectory with
  official `submission.parquet`.
- [Humanity's Last Exam](Language-Games-HLE) — CAIS question-bound exact
  answers and official judging.

These pages explain contracts and readiness checks. They do not invent scores.

## One game, three answer languages

```text
official question state → Affine context state → validated answer artifact → official evaluator
```

| Track | Question state | Typed answer | Win condition |
| --- | --- | --- | --- |
| ARC-AGI-2 | Training grid pairs and held-out grids | Two rectangular candidate grids in JSON | Exact hidden-grid match |
| ARC-AGI-3 | Environment observation and retained episode history | One legal action each turn, then official parquet | Official episode evaluator |
| HLE | Official record, answer format, and supported modalities | Normalized final answer bound to question ID | Official CAIS judge |

Explanations may support reasoning, but the typed artifact is the evaluated
move.

## Shared invariants

1. **Identity:** task, episode, and question IDs survive from input to output.
2. **Complete context:** full demonstrations, trajectory state, or HLE record
   is established before answering.
3. **Typed output:** grids, actions, and exact-answer fields preserve their
   exam-defined types.
4. **External state authority:** datasets determine labels, environments
   determine next state, and the CAIS judge determines metrics.
5. **Artifact provenance:** JSON, parquet, and prediction files serialize the
   locally validated state without key/order/format drift.
6. **Evidence honesty:** local validation proves readiness; only official
   receipts prove public results.

## Context-to-answer protocol

1. Bind official identity, version/revision, complete context, and answer
   contract.
2. Parse into the track-native state model.
3. Restrict output to moves legal under that model.
4. Run track-specific local validation.
5. Serialize through the official adapter with provenance.
6. Save a green preflight receipt.
7. Treat platform/judge output as the only source of public score status.

## Drift taxonomy

| Drift | Meaning | Required action |
| --- | --- | --- |
| Exam-spec drift | Official schema, API, dataset, action, or judge contract changed | Update adapter/validator and rerun preflight |
| Understanding drift | Stable official contract but incorrect inferred move | Repair task-native reasoning |
| Serialization drift | Valid internal state differs from emitted artifact | Repair adapter and prove equality |
| Evidence drift | Local result presented as public score | Restore correct label and cite receipt |

## Affine.Earth UI language games

| UI layer | Exam responsibility |
| --- | --- |
| Linguistic membrane | Preserve full question context and answer language |
| Formal | Bind identity, state type, legal transitions, and acceptance criteria |
| Coding | Run official adapters/harnesses, validate artifacts, retain receipts |

## Hard gate

**No public Kaggle or HLE submission occurs until the relevant local validators
are green and a preflight receipt exists.** Green local checks establish
readiness only. Public scores require the corresponding Kaggle or CAIS receipt.
