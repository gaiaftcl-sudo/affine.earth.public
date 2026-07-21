# Language Game: ARC Prize 2026 — ARC-AGI-2

This is pre-submission technical doctrine for the public test repository. It
describes the official ARC-AGI-2 task contract and the local checks required
before any further Kaggle submission. It does not claim a score.

Official competition: <https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-2>

## 1. The game

ARC-AGI-2 presents a finite set of demonstrations followed by one test input.
Each demonstration is a move of the form:

```text
input grid ──[latent transformation]──> output grid
```

The solver's turn is to infer one transformation that is consistent with all
training moves, apply that transformation to the test grid, and write two
ranked candidate outputs. The evaluator's turn is exact grid comparison. The
win condition is an exact match for either `attempt_1` or `attempt_2`; color,
cell coordinate, grid dimensions, and JSON nesting are all part of the move.

The language game is therefore not “describe a plausible visual pattern.” It
is a constrained program-induction exchange:

1. Observe every input/output demonstration without changing its coordinate
   system.
2. State a transformation hypothesis in an internal, executable form.
3. Reject hypotheses contradicted by any demonstration.
4. Apply a surviving hypothesis to the held-out input.
5. Emit two concrete grid candidates in the official schema.

## 2. Input, output, and state

| Element | Contract |
| --- | --- |
| Training state | One or more `{input, output}` integer grids. |
| Test state | One or more input grids with outputs withheld. |
| Cell alphabet | Integer colors in the official ARC encoding; values are symbols, not numeric magnitudes. |
| Spatial state | Rectangular dimensions, row/column order, connected components, symmetries, and object relations. |
| Output state | `submission.json`, keyed by task id; every test item carries `attempt_1` and `attempt_2` as rectangular integer grids. |
| Evaluation | Exact match of a candidate grid to the hidden target. |

The submission adapter must preserve task IDs, test-item ordering, and
rectangular rows. A correct transformation with a changed task key, a missing
attempt, or an invalid grid is not a valid move in the competition game.

## 3. Communication invariants for Affine

The linguistic membrane must preserve these facts from question context to
answer state:

1. **Observation provenance:** every proposed output must be traceable to the
   complete training set for that task, never a prompt fragment or a
   cross-task prior.
2. **Coordinate integrity:** row/column origin, orientation, and grid
   dimensions remain stable unless the demonstrations require a resize.
3. **Symbol integrity:** colors are discrete labels. Do not treat a color ID
   as a magnitude or replace it with prose.
4. **Object identity:** connected components, bounding boxes, counts,
   repeated motifs, and relations are explicit state, not implicit visual
   impressions.
5. **Hypothesis consistency:** a candidate rule must reproduce every training
   output exactly before it may generate a test answer.
6. **Serialization integrity:** the final structured answer must be the same
   grid state the solver validated locally.

## 4. Context-setting protocol

Before answering a test item, form a task ledger:

1. Parse each training pair into dimensions, background candidates, components,
   color inventory, and coordinate relations.
2. Diff each input/output pair to identify additions, removals, recolors,
   translations, reflections, rotations, crops, tilings, or counting rules.
3. Express candidate transformations as deterministic operations over grid
   state, including preconditions and an output-size rule.
4. Execute each candidate against *all* training inputs; retain only exact
   reproductions.
5. Resolve ambiguity by ranking rules that use demonstrated invariants rather
   than unobserved assumptions. Keep the two strongest distinct executable
   candidates where ambiguity remains.
6. Apply candidates to the test input and verify each produced grid is
   rectangular and uses the permitted symbol domain.

This protocol separates question comprehension from answer emission. An answer
is released only after the full training context has been consumed and
replayed.

## 5. Formal question-to-answer state change

Let a task be `T = (D, X)`, where `D = {(x_i, y_i)}` is the demonstration set
and `X` is the test-input sequence. Let `H` be the candidate transformation
space. A valid candidate is:

```text
h ∈ H such that ∀(x_i, y_i) ∈ D, h(x_i) = y_i
```

The answer transition is:

```text
(D, X, h1, h2) → {
  task_id: [{attempt_1: h1(x), attempt_2: h2(x)} for x in X]
}
```

with `h1` and `h2` both locally replayed against `D`. The result is not
licensed by narrative plausibility; it is licensed by exact demonstration
reproduction plus schema validity.

## 6. Local drift checks

Local validation distinguishes a changed official contract from a bad
interpretation:

| Check | Detects |
| --- | --- |
| Official-data schema validator | Missing task IDs, missing attempts, malformed JSON, invalid grids, or changed competition schema. |
| Demonstration replay | A transformation that does not actually explain the stated question. |
| Task-count and test-count comparison | Stale or partial official data. |
| Output key/order comparison | Adapter drift between solver state and submission state. |
| Grid shape and integer-domain check | Serialization corruption. |
| Offline held-out exact-match evaluation, when labels exist | Local solver quality; it is not a Kaggle score. |
| Submission preflight receipt | Evidence that all checks were green before a public action. |

If the schema or official dataset changes, treat it as **exam-spec drift** and
update the adapter and validator. If the schema is stable but replay fails,
treat it as **solver-understanding drift** and do not submit.

## 7. Affine.Earth UI language-game mapping

| UI game | ARC-AGI-2 role |
| --- | --- |
| Linguistic membrane | Captures the complete task, preserves symbols and coordinates, and makes ambiguous observations explicit. |
| Formal game | Converts observations into executable candidate transformations and replays them across demonstrations. |
| Coding game | Materializes grids into the official `attempt_1` / `attempt_2` JSON contract and runs the preflight validator. |

The UI may show explanations, but those explanations are not the submission.
The submission is the validated structured grid state.

## 8. Submission gate

**No public ARC-AGI-2 Kaggle submission is permitted until local validators are
green.** The minimum green set is official-data schema validation,
demonstration replay for every produced candidate, output serialization
validation, and a saved preflight receipt. A local result must be described as
local until Kaggle publishes a score receipt.
