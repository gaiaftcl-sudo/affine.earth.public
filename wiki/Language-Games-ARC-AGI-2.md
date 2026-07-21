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

**MEASURED local** (2026-07-21): evaluation lifts to **56/172** exact grids
(overlay `reports/arc_local_20260721T162654Z/agi2/summary-overlay.json`;
train ice-on baseline remains **298/1076**). Lineage includes
`s1_panel_motif_projection` **4c7dc4dd** ×2 → `s1_motif_stamp_jigsaw` **4e34c42c** ×2 → `s3_terrain_period_bounce` **195c6913** ×2 → `s1_solid_motif_carve` **58f5dbd5** ×1 → `s2_plus_stamp_recolor` **1818057f** ×1 → `s1_path_column_unroll` **7b5033c1** ×1 → `s1_ones_stamp_period_fill` **53fb4810** ×1 → `s1_canvas_hole_sprite_fill` **67e490f4** ×1 → `s1_panel_motif_nest_pack` **8698868d** ×1 → `s1_separator_block_unroll` **78332cb0** ×2 → `s1_sep_row_extent_sort` **31f7f899** ×1 → `s1_frame_chamber_staircase` **89565ca0** ×1 → `s1_header_bracket_fill` **97d7923e** ×1 → `s2_arrow_room_recolor` **21897d95** ×2 → `s2_marker_stripe_lattice` **221dfab4** ×2 → `s2_axis_glyph_stamp` **247ef758** ×2 → `s3_box_slide_rail_fill` **271d71e2** ×1 → `s3_staircase_interior_fill` **28a6681f** ×1 → `s2_seven_triplet_rail` **2b83f449** ×1 → `s3_cross_arm_shape_dock` **2c181942** ×1 = **56/172**.

| Owned grammar | Engine | Train replay | Eval |
| --- | --- | --- | --- |
| marker-8 twin-S | `marker8_twin31` | 4/4 on `0934a4d8` | exact |
| hollow/solid object pack | `s1_dimension_projection` | 4/4 on `2ba387bc` | exact |
| band concentric nest | `s1_dimension_projection` | 2/2 on `45a5af55` | exact ×1 |
| digit-separator snake | `s1_digit_separator_snake` | 3/3 on `136b0064` | exact |
| seven-tab merge | `s1_seven_tab_merge` | 4/4 on `20270e3b` | exact ×2 |
| panel odd-one-out | `s1_panel_odd_one_out` | 2/2 on `38007db0` | exact ×2 |
| marker-frame motif | `s1_marker_frame_motif` | 3/3 on `20a9e565` | exact ×2 |
| fixed-canvas template | `s1_fixed_canvas_template` | 5/5 on `269e22fb` | exact ×2 |
| wall-tree nested frames | `s1_wall_tree_nested_frames` | 3/3 on `13e47133` | exact ×2 |
| laser-mirror beams | `s1_laser_mirror_beams` | 3/3 on `142ca369` | exact ×2 |
| oriented block pack | `s1_oriented_block_pack` | 4/4 on `291dc1e1` | exact ×1 |
| panel motif projection | `s1_panel_motif_projection` | 2/2 on `4c7dc4dd` | exact ×2 |
| motif stamp jigsaw | `s1_motif_stamp_jigsaw` | 2/2 on `4e34c42c` | exact ×2 |
| zero-panel motif-count | `s1_zero_panel_motif_count` | 3/3 on `58490d8a` | exact ×1 |
| topology schematic | `s1_topology_schematic` | 4/4 on `2d0172a1` | exact ×2 |
| hollow accent-fill | `s1_hollow_accent_fill` | 2/2 on `3a25b0d8` | exact ×2 |
| container period tiling | `container_period_tiling` | 2/2 on `135a2760` | exact |
| separator ray-fill | `s3_separator_ray_fill` | 3/3 on `1ae2feb7` | exact ×3 |
| separator gap-stack | `s3_separator_gap_stack` | 2/2 on `16b78196` | exact ×1 |
| period lattice rewrite | `s3_period_lattice_rewrite` | 3/3 on `16de56c4` | exact ×2 |
| legend motif tally | `s1_legend_motif_tally` | 3/3 on `58490d8a` | exact ×1 |
| terrain period-bounce | `s3_terrain_period_bounce` | 3/3 on `195c6913` | exact ×2 |
| solid-motif carve | `s1_solid_motif_carve` | 3/3 on `58f5dbd5` | exact ×1 |
| plus-stamp recolor | `s2_plus_stamp_recolor` | 3/3 on `1818057f` | exact ×1 |
| path-column unroll | `s1_path_column_unroll` | 2/2 on `7b5033c1` | exact ×1 |
| ones-stamp period fill | `s1_ones_stamp_period_fill` | 2/2 on `53fb4810` | exact ×1 |
| canvas-hole sprite fill | `s1_canvas_hole_sprite_fill` | 2/2 on `67e490f4` | exact ×1 |
| panel-motif nest pack | `s1_panel_motif_nest_pack` | 2/2 on `8698868d` | exact ×1 |
| separator-block unroll | `s1_separator_block_unroll` | 3/3 on `78332cb0` | exact ×2 |
| sep-row extent sort | `s1_sep_row_extent_sort` | 3/3 on `31f7f899` | exact ×1 |
| header-bracket fill | `s1_header_bracket_fill` | 3/3 on `97d7923e` | exact ×1 |
| frame-chamber staircase | `s1_frame_chamber_staircase` | 3/3 on `89565ca0` | exact ×1 |
| staircase interior fill | `s3_staircase_interior_fill` | 3/3 on `28a6681f` | exact ×1 |
| seven-triplet rail | `s2_seven_triplet_rail` | 2/2 on `2b83f449` | exact ×1 |
| cross-arm shape dock | `s3_cross_arm_shape_dock` | 3/3 on `2c181942` | exact ×1 |
| ice+DSL residual | `arc-icecuber` hybrid | n/a | +1 prior (`981571dc`) |

**S1 grammar (`hollow_solid_object_pack`):**

- **S1:** output canvas size ≠ input (packed object grid).
- **S2:** equal-size connected components partition into hollow frames vs solid fills.
- **S3:** each partition sorted by source row; packed two columns wide.
- **S4:** left = hollow, right = solid.
- **C4:** exact packed grid; licensed only when every training pair replays.


**S1 grammar (`motif_stamp_jigsaw` / `4e34c42c`):**

- **S1:** majority color = background; remaining cells form 4-connected stamps.
- **S2:** drop stamps that are exact subarrays of a larger stamp bbox crop.
- **S3:** assemble by consistent 2D overlap offsets (`min_ov=3`); maximize total overlap, then minimize bbox area.
- **S4:** output collage with background fill in unpainted cells.
- **C4:** exact collage; train-replay gated (`2/2`, eval `2/2`).

**S1 grammar (`band_concentric_nest` / `45a5af55`):**

- **S1:** larger square output from full-width uniform row-band input.
- **S2:** bands = maximal runs of identical solid rows `(color, thickness)`.
- **S3:** each outer band becomes a concentric frame of the same thickness.
- **S4:** last band fills the center; `size = 2*sum(t[:-1]) + t[-1]`.
- **C4:** exact nest; train-replay gated (`2/2`, eval `1/1`).

**S1 grammar (`digit_separator_snake` / `136b0064`):**

- **S1:** drop sep+right → 7-wide canvas; marker `5` preserved.
- **S2:** left panels = paired 3×3 digits; sequence = left-column then right-column.
- **C4:** typed port attachment snake (1→right port; 2/3/6→left/sole; seat 1/6 on
  port, 2/3 right-aligned on port). Train **3/3**.

**S1 grammar (`wall_tree_nested_frames` / `13e47133`):**

- **S1:** majority color = room fill background; full-height/width uniform non-bg
  separator = wall tree that partitions rooms.
- **S2:** each 4-connected non-wall component is a room (may be C-shaped).
- **S3:** room depth = Chebyshev distance from the 8-neighbor boundary.
- **S4:** non-bg seeds at depth `d` set `period[d]`; missing depth-0 seed injects bg;
  contiguous period from 0 cycles for deeper rings.
- **C4:** walls preserved; every room cell colored by `period[depth % len]`;
  train-replay gated. Train **3/3**, labeled eval **2/2**.

Franklin REINJECT root cause: typed candidates reused truncated `expected_preview`
(8×12) / shape confusion vs 30×30 inputs — rejected by `demonstration_replay`.

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


**S3 grammar (`period_lattice_rewrite` / `16de56c4`):**

- **S1:** same canvas shape (in-place rewrite).
- **S2:** axis = rows if more multi-seed rows than cols, else cols.
- **S3:** mono → full gcd lattice; pattern+singleton on-lattice → recolor `[min,max]`; else extend pattern + keep singleton.
- **S4:** lines with <2 seeds unchanged.
- **C4:** exact rewrite; train-replay gated (`3/3`, eval `2/2`).

**S1 grammar (`legend_motif_tally` / `58490d8a`):**

- **S1:** majority color = main bg; largest mostly-zero panel = legend crop.
- **S2:** legend markers = unique nonzero colors on that crop.
- **S3:** for each marker color, count 8-connected components in main (legend masked to bg).
- **S4:** emit legend-shaped zeros; place `count` copies at `marker_col + 2k` on the marker row.
- **C4:** exact tally crop; train-replay gated (`3/3`, eval `1/1`).


**S1 grammar (`zero_panel_motif_count` / `58490d8a`):**

- **S1:** majority wall; output canvas = bbox of all 0-cells.
- **S2:** panel markers = nonzero non-wall cells in that bbox.
- **S3:** for marker color C, count 8-connected outside C-motifs; paint C at `col+2k` for `k=0..count-1`.
- **S4:** other panel cells stay 0.
- **C4:** exact panel; train-replay gated (`3/3`, eval `1/1`).

**S1 grammar (`solid_motif_carve` / `58f5dbd5`):**

- **S1:** majority color = background; filled rectangles (h,w ≥ 4) are solids.
- **S2:** for each solid color C, non-solid C cells form a motif mask (bbox).
- **S3:** motif size `(solid_h-2)×(solid_w-2)`; punch motif-present cells in the solid interior to background.
- **S4:** output = crop covering all solids expanded by one bg frame cell.
- **C4:** exact pack; train-replay gated (`3/3`, eval `1/1`).

**S1 grammar (`canvas_hole_sprite_fill` / `67e490f4`):**

- **S1:** majority color = background; largest non-bg component = canvas.
- **S2:** output crop = canvas bbox; canvas cells kept; bg cells are holes.
- **S3:** non-canvas sprites vote by mask class (4-rotations × mirrors).
- **S4:** each hole fills with the majority sprite color for that mask class.
- **C4:** exact filled crop; train-replay gated (`2/2`, eval `1/1`).

## FoT: S2 arrow-room recolor — `21897d95`

Train **4/4**, eval **2/2** via `s2_arrow_room_recolor`. Mastery **48/172**. No Kaggle.

## FoT: S2 marker-stripe lattice — `221dfab4`

Train **2/2**, eval **2/2** via `s2_marker_stripe_lattice`. Mastery **52/172**. No Kaggle.

## FoT: S2 axis-glyph stamp — `247ef758`

Train **3/3**, eval **2/2** via `s2_axis_glyph_stamp`. Mastery **52/172**. No Kaggle.

## FoT: S3 box-slide rail-fill — `271d71e2`

Train **3/3**, eval **1/1** via `s3_box_slide_rail_fill`. Mastery **53/172**. No Kaggle.

## 271d71e2 — box_slide_rail_fill (S3)

C4: BG=6; 0-bordered boxes slide min(rail_gap, n_grey) along maroon rails; refill 7 then 5 by direction. Train 3/3, eval 1/1. Module `llm_llvm_bench/arc/s3_box_slide_rail_fill.py`. No Kaggle.

## FoT: S3 staircase interior fill — `28a6681f`

Train **3/3**, eval **1/1** via `s3_staircase_interior_fill`. Mastery **54/172**. No Kaggle.

## 28a6681f — staircase_interior_fill (S3)

C4: BG=0; blue(1) conserved; Type A same-color L/R gaps from floor; Type B open left extensions; fill A then B bottom-up to N. Train 3/3, eval 1/1. Module `llm_llvm_bench/arc/s3_staircase_interior_fill.py`. No Kaggle.

## FoT: S2 seven-triplet rail — `2b83f449`

Train **2/2**, eval **1/1** via `s2_seven_triplet_rail`. Mastery **55/172**. No Kaggle.

## 2b83f449 — seven_triplet_rail (S2)

C4: odd-row 777→868; even rails paint 6 at triplet centers; redistribute 3s to segment edges; suppress conflicts across 0-boundaries. Train 2/2, eval 1/1. Module `llm_llvm_bench/arc/s2_seven_triplet_rail.py`. No Kaggle.

## FoT: S3 cross-arm shape dock — `2c181942`

Train **3/3**, eval **1/1** via `s3_cross_arm_shape_dock`. Mastery **56/172**. No Kaggle.

## 2c181942 — cross_arm_shape_dock (S3)

C4: BG=8; 4×4 four-arm cross; rotate/dock same-color shapes onto arms by longest matching face. Train 3/3, eval 1/1. Module `llm_llvm_bench/arc/s3_cross_arm_shape_dock.py`. No Kaggle.

