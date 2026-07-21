# Language Games — Exam Invariants

This is the pre-submission hub for the three public exam tracks:

- [ARC-AGI-2](Language-Games-ARC-AGI-2) — static grid transformation with
  `attempt_1` / `attempt_2`.
- [ARC-AGI-3](Language-Games-ARC-AGI-3) — interactive agent trajectory with
  official `submission.parquet`.
- [Humanity's Last Exam](Language-Games-HLE) — CAIS question-bound exact
  answers and official judging.

These pages explain contracts and readiness checks. They do not invent scores.

**Franklin absolute execution baseline:**
[UUM-8D game comprehension & bond resolution](../docs/FRANKLIN_UUM8D_GAME_COMPREHENSION_SYSTEM_PROMPT.md)
— immutable root system instruction for HLE / ARC-AGI language games
(constraint-satisfaction / Jordan bond; not probabilistic guessing).

**Permanent miss → reinject → closure loop:**
[Exam Miss → Reinject → Closure](Exam-Miss-Reinjection-Loop) —
`bin/run-exam-reinjection-loop.sh` loads local fail receipts, opens Franklin
turns for S1–S4 repair + C4 lock, re-runs local mastery, and logs progress
toward 29-turn Aristotelian closure. Never idles. Never Kaggle-submits.
Doctrine: [`docs/EXAM_MISS_REINJECTION_LOOP.md`](../docs/EXAM_MISS_REINJECTION_LOOP.md).

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

## Production local audit path

[ARC UI Audit Orchestrator](ARC-UI-Audit-Orchestrator) is the production ARC
path: every task owns a complete context injection, local UI audit MP4, strict
typed artifact, and receipt. It preserves the six shared invariants at the
actual Cursor interaction boundary. The bridge is an actual configured local
HTTP call or an explicit `AWAITING_CELL_BRIDGE` receipt; it never manufactures
an answer. `configs/NO_KAGGLE_SUBMIT.lock` remains mandatory.

## Hard gate

**No public Kaggle or HLE submission occurs until the relevant local validators
are green and a preflight receipt exists.** Green local checks establish
readiness only. Public scores require the corresponding Kaggle or CAIS receipt.

## ARC UI audit gate

For ARC tracks, the local preflight includes the
[ARC UI Audit Orchestrator](ARC-UI-Audit-Orchestrator): macOS permissions,
VideoToolbox capture, task-bound Cursor prompt injection, nine-cell reduction,
JSON extraction, clean `SIGINT` capture stop, and track-native artifact
validation. The final audit receipt must be GREEN **before any Kaggle
submission**.

`configs/NO_KAGGLE_SUBMIT.lock` remains present while that audit runs. The
audit cannot remove the lock, turn a local receipt into a public result, or
replace explicit steward authorization. Earlier **0.00** / **0.12** Kaggle
process probes established artifact delivery only; they do not satisfy this
current local-audit gate.

## Format from top scores

Reverse-engineered artifact contracts (with FoT contrast of our AGI-3
**publicScore 0.12** vs LB ~1.86):
[Kaggle-ARC-Top-Score-Formats](Kaggle-ARC-Top-Score-Formats). Those examples
are the **serialization** of the state changes defined on the ARC-AGI-2 /
ARC-AGI-3 language-game pages — not a substitute for puzzle mastery.
