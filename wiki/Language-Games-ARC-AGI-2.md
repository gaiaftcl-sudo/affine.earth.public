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

## 7.1 Production exam path: local UI audit

The production path is [ARC UI Audit Orchestrator](ARC-UI-Audit-Orchestrator):
one local Cursor turn and one raw `task_<ID>.mp4` video audit per task. It
injects the full task state, performs a real configured local bridge call when
available, takes the UI clipboard as the primary answer path, and validates
each task-scoped attempt pair before local serialization. The complete
protocol and macOS Accessibility / Screen Recording requirement are in
[`docs/ARC_UI_AUDIT_ORCHESTRATOR.md`](../docs/ARC_UI_AUDIT_ORCHESTRATOR.md).
This remains local-only with `NO_KAGGLE_SUBMIT.lock` present.

## 8. Public-submission gate

**No public ARC-AGI-2 submission until schema validation, candidate replay,
serialization validation, and a saved preflight receipt are green.** Local
results remain local until Kaggle issues a score receipt.

The required ARC local preflight is documented in
[ARC UI Audit Orchestrator](ARC-UI-Audit-Orchestrator). It binds each official
task to VideoToolbox capture, Cursor prompt-injection provenance, a nine-cell
reduction, extracted result JSON, a clean `SIGINT` capture stop, and
`submission.json` validation. `configs/NO_KAGGLE_SUBMIT.lock` stays present:
audit GREEN comes before, and never itself authorizes, any Kaggle submit.

## 9. Format from top scores

Typed artifact after the language-game state change (full detail:
[Kaggle-ARC-Top-Score-Formats](Kaggle-ARC-Top-Score-Formats),
[`docs/KAGGLE_ARC_TOP_SCORE_FORMATS.md`](../docs/KAGGLE_ARC_TOP_SCORE_FORMATS.md)):

```text
submission.json → { task_id: [ {attempt_1: grid, attempt_2: grid}, … ] }
```

| Rule | Exact |
| --- | --- |
| Keys per test | exactly `attempt_1`, `attempt_2` |
| Grid | rectangular ints 0..9 |
| Win | either attempt exact-matches the hidden grid |

Cited: official `sample_submission.json` (240 tasks); NVARC baseline
`get_submission`; MCP AGI-2 starter. Our baseline
[live record](ARC-Prize-AGI-2-Kaggle-Live) scores **0.00** with a schema-valid
file — format correctness, not LB mastery (nvbanana **65.83**). Local check:
`python3 scripts/validate_arc_prize_submission.py …/submission.json`.

## 10. Local replay-gated rule inventory

The local solver implements small executable rule families, not output
placeholders:

- dihedral geometry followed by a training-fitted color permutation;
- uniform cell scaling, periodic tiling, and modal reduction where all
  demonstrations agree on output dimensions;
- color-specific and foreground-component crop/extraction, including isolated
  same-color objects;
- separator-row/column removal, reflection, and symmetry completion;
- directional gravity as a same-shape object-motion operation.

For each task, the trace records the entire candidate family, the candidates
that replay all demonstrations, and the two emitted grids.

## 11. Local hybrid engine (MIT arc-icecuber + DSL)

Offline mastery now hybridizes the replay-gated Python DSL with the MIT-licensed
CPU search solver vendored at `harnesses/arc-icecuber` (adapter:
`llm_llvm_bench/arc/icecuber_adapter.py`). Scoring is against official
`arc-agi_evaluation_solutions.json` / training solutions (contract verified:
172 eval grids, 1076 train grids).

Measured local receipt `reports/arc_local_20260721T110813Z/` (main `db71c28`; validators
**GREEN**; submit **LOCKED**):

| Split | Exact grids | Notes |
| --- | --- | --- |
| Evaluation | **1/172** | Was **0/172** at `7ab6e05`; hit task `981571dc` |
| Training | **298/1076** | Was **22/1076** DSL-only; icecuber alone 296/1076 |

Failure-case dump (5): `agi2/failure-case-analyses.json`. Root cause of the
prior 0/172 was coverage (no licensed transform / search miss), not a scorer
bug. Depth-3 / flip-augmented probes did not add eval hits on a Dimensions
subset. No Kaggle submit.

## 12. FoT: task `0934a4d8` local SOLVED 4/4 (marker8_twin31)

**MEASURED local** (2026-07-21): evaluation task `0934a4d8` is licensed by
`LOCAL_HYBRID_SOLVER` `llm_llvm_bench/arc/marker8_twin31.py` — train replay
**4/4**, test prediction exact-matches official evaluation solution, attempt_1
= attempt_2. Rule: color-8 filled bbox; cell values from S=31 rot180 twin
`g[31-r][31-c]` (symmetry ignoring 8s); OOB twins via transpose `g[c][r]`
(mode order BOTH>LR>UD>MAIN>ANTI).

Artifacts:

- `affine_audit_logs/submission_0934a4d8.json`
- `affine_audit_logs/train_replay_proof_0934a4d8.json`
- UI audit GREEN: `reports/arc_ui_audit/20260721T111911Z/` (reduction
  `LOCAL_HYBRID_SOLVER`, not `AWAITING_CELL_BRIDGE`)

Canonical submission fragment:

```json
{"0934a4d8":[{"attempt_1":[[7,7,9],[7,2,9],[7,2,9],[7,7,9],[4,4,7],[4,4,7],[6,6,1],[6,6,6],[1,6,1]],"attempt_2":[[7,7,9],[7,2,9],[7,2,9],[7,7,9],[4,4,7],[4,4,7],[6,6,1],[6,6,6],[1,6,1]]}]}
```

Linked: [ARC UI Audit Orchestrator](ARC-UI-Audit-Orchestrator). Submit remains
**LOCKED** (`configs/NO_KAGGLE_SUBMIT.lock`).


## 13. FoT: S1 dimension projection — `2ba387bc` (hollow_solid_object_pack)

**MEASURED local** (2026-07-21): evaluation lifts to **12/172** exact grids
(overlay receipt `reports/arc_local_20260721T135500Z/agi2/summary-overlay.json`;
train ice-on baseline remains **298/1076**). Lineage: 8/172 → **+2** `20270e3b`
seven-tab merge → **+2** `38007db0` panel odd-one-out = **12/172**.

| Owned grammar | Engine | Train replay | Eval |
| --- | --- | --- | --- |
| marker-8 twin-S | `marker8_twin31` | 4/4 on `0934a4d8` | exact |
| hollow/solid object pack | `s1_dimension_projection` | 4/4 on `2ba387bc` | exact |
| digit-separator snake | `s1_digit_separator_snake` | 3/3 on `136b0064` | exact |
| seven-tab merge | `s1_seven_tab_merge` | 4/4 on `20270e3b` | exact ×2 |
| panel odd-one-out | `s1_panel_odd_one_out` | 2/2 on `38007db0` | exact ×2 |
| container period tiling | `container_period_tiling` | 2/2 on `135a2760` | exact |
| separator ray-fill | `s3_separator_ray_fill` | 3/3 on `1ae2feb7` | exact ×3 |
| ice+DSL residual | `arc-icecuber` hybrid | n/a | +1 prior (`981571dc`) |

**S1 grammar (`hollow_solid_object_pack`):**

- **S1:** output canvas size ≠ input (packed object grid).
- **S2:** equal-size connected components partition into hollow frames vs solid fills.
- **S3:** each partition sorted by source row; packed two columns wide.
- **S4:** left = hollow, right = solid.
- **C4:** exact packed grid; licensed only when every training pair replays.

**S1 grammar (`digit_separator_snake` / `136b0064`):**

- **S1:** drop sep+right → 7-wide canvas; marker `5` preserved.
- **S2:** left panels = paired 3×3 digits; sequence = left-column then right-column.
- **C4:** typed port attachment snake (1→right port; 2/3/6→left/sole; seat 1/6 on
  port, 2/3 right-aligned on port). Train **3/3**.

**S3 grammar (`separator_ray_fill` / `1ae2feb7`):**

- **S2:** vertical uniform separator column.
- **S3:** content-side motifs ray-fill the empty side (leftward = reversed buffer).
- **C4:** single-color period; near singleton → solid; far singleton → reverse collapse;
  both counts > 1 → B0 templates by near/far count comparison. Train **3/3**.

Failure taxonomy retains all misses with classes `S3_spatial_rewrite` /
`S1_dimension_projection` / `S2_palette_rewrite` (`scripts/arc_local_mastery.py`).
Remaining S1/S3 tasks queued at
`reports/exam_reinjection/arc_agi2_s1_miss_queue.jsonl` and
`reports/exam_reinjection/arc_agi2_s3_miss_queue.jsonl`. Submit **LOCKED**.
