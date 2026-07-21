# Language Games — ARC-AGI-2

Pre-submission specification for [ARC Prize 2026 — ARC-AGI-2](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-2). This page explains the contract; it does not claim a score.

## 1. Game, moves, and win condition

Each task supplies input/output grid demonstrations and one or more withheld
test grids. The solver must infer a single executable transformation that
reproduces all demonstrations, then emit two ranked test-grid candidates.
Kaggle wins an item only when `attempt_1` or `attempt_2` exactly equals the
hidden grid. Dimensions, color labels, coordinates, task keys, and JSON shape
are all part of the move.

## 2. Input/output state

- Input: `{input, output}` integer-grid training pairs plus test input grids.
- State: grid dimensions, discrete color labels, components, object relations,
  symmetry, and the candidate transformation.
- Output: official `submission.json`, keyed by task ID, with rectangular
  `attempt_1` and `attempt_2` grids for every test item.
- Evaluation: exact hidden-grid match; an explanation is not an output grid.

## 3. Affine communication invariants

The linguistic membrane preserves full training provenance, coordinate
orientation, color-as-symbol semantics, object identity, and the task ID.
Every candidate must replay every training pair exactly, and the serialized
JSON must carry the same validated grid state.

## 4. Context-setting protocol

1. Parse every training pair into geometry, components, color inventory, and
   input/output delta.
2. Express candidate rules as deterministic grid operations with
   preconditions and output-size rules.
3. Replay each rule against *all* demonstrations.
4. Rank only exact-replay candidates; retain two distinct candidates only
   when ambiguity remains.
5. Apply to the test grid, then validate shape, colors, ordering, and keys.

## 5. Formal state transition

For demonstrations `D = {(x_i, y_i)}`, candidate space `H`, and test inputs
`X`, a candidate is valid only when:

```text
h ∈ H and ∀(x_i, y_i) ∈ D: h(x_i) = y_i
```

The answer is:

```text
(D, X, h1, h2) → { task_id: [{attempt_1: h1(x), attempt_2: h2(x)}] }
```

Neither candidate is licensed by visual plausibility alone.

## 6. Local drift checks

| Check | Distinguishes |
| --- | --- |
| Official schema/task-count validator | Changed competition data or JSON contract |
| Demonstration replay | Incorrect task interpretation |
| Key/order and grid-shape validator | Solver-to-adapter serialization drift |
| Offline held-out evaluation | Local quality only, never a Kaggle score |
| Preflight receipt | Evidence local validators were green |

Changed schema/data is exam-spec drift. Stable schema with replay failure is
understanding drift.

## 7. Affine UI mapping

- **Linguistic membrane:** preserves full demonstrations and spatial symbols.
- **Formal:** represents transformations and exact-replay constraints.
- **Coding:** writes and validates the official `attempt_1` / `attempt_2`
  artifact.

## 8. Public-submission gate

**No public ARC-AGI-2 submission until schema validation, candidate replay,
serialization validation, and a saved preflight receipt are green.** Local
results remain local until Kaggle issues a score receipt.
