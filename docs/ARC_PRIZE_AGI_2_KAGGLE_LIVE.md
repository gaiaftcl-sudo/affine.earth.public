# ARC Prize 2026 (ARC-AGI-2) — Kaggle live record

Official competition: [ARC Prize 2026 — ARC-AGI-2](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-2)

**Submit status:** **BLOCKED** — `configs/NO_KAGGLE_SUBMIT.lock`. No new Kaggle submits until local mastery is green **and** the steward sets `ALLOW_KAGGLE_SUBMIT=1`.

## LOCAL mastery gate (required before any future submit)

| Gate | Result |
|:---|:---|
| Language-game doctrine | [Language-Games-ARC-AGI-2](Language-Games-ARC-AGI-2) · hub [Exam Invariants](Language-Games-Exam-Invariants) (`f983986`) |
| Top-score format study | [Kaggle-ARC-Top-Score-Formats](Kaggle-ARC-Top-Score-Formats) (`a04e483`) |
| Hard schema validator | `scripts/validate_arc_prize_submission.py` on fixture + official sample + local `submission.json` vs test challenges |
| Local harness | `bin/run-arc-local-mastery.sh` → `reports/arc_local_20260721T110813Z/` **overall GREEN** |
| Eval quality (local) | **42/172** exact grids (S1 family + panel-motif nest pack + canvas-hole sprite fill + ones-stamp period fill + path-column unroll + plus-stamp recolor + legend motif tally + motif stamp jigsaw + band concentric nest + hollow accent-fill + topology schematic + separator gap-stack + fixed-canvas + wall-tree + marker-frame + CPT + S3 + ice/DSL) |
| Train quality (local) | **298/1076** exact grids (ice-on receipt); **24/1000** DSL-licensed tasks |
| Engine | `LOCAL_HYBRID_SOLVER` = marker8 + S1 family (pack/snake/tab/panel/motif/canvas/wall-tree/laser/block-pack/topology/hollow-accent) + CPT + S3 ray-fill/gap-stack + icecuber + DSL |
| Public probe | publicScore **0.00** = **PROCESS_PROBE** (premature process test) |
| LB contrast | Top public ~**65.83** — format≠mastery; local eval still far from LB |

```bash
./bin/run-arc-local-mastery.sh
# Emits reports/arc_local_*/agi2/submission.json (240 tasks) + language-game traces
# Never: kaggle competitions submit  (lock present)
```

UI context (Affine Formal/membrane — ARC grid exam not hosted in UI yet):

![Exam UI context](assets/exam-ui-arc-context.png)

![ARC-AGI-2 doctrine](assets/exam-ui-arc-agi2-doctrine.png)

## Recorded 2026-07-21

| Check | Observed result |
|:---|:---|
| Competition entry | **Entered** — Kaggle reports `userHasEntered=True` |
| Official data | **Downloaded** — 240 test tasks, 120 evaluation tasks, and 1,000 training tasks |
| Package | `kaggle/arc-prize-2026-agi-2/` on `main`; public-repo code only |
| Submission contract | `submission.json` with `attempt_1` + `attempt_2` for every official test grid |
| Notebook | [Affine ARC Prize 2026 — ARC-AGI-2](https://www.kaggle.com/code/bliztafree/affine-arc-prize-2026-agi-2), **complete**, internet disabled |
| Competition submission | v1 was **accepted**; further submits **blocked** by lock |
| **Public score** | **0.00** — `SubmissionStatus.COMPLETE` — mark as **premature process probe** |

The package is separate from the ARC-AGI-3 notebook and contains no credentials
or private affine.earth OS source.

## Evidence

- Local schema validation: 240 official test tasks (hard gate green).
- Offline evaluation set: **56/172** exact grids (cross-arm shape dock + seven-triplet rail + staircase interior fill + box-slide rail-fill + marker8 + S1 family + axis-glyph stamp + marker-stripe lattice + arrow-room recolor + header-bracket fill + frame-chamber staircase + sep-row extent sort + separator-block unroll + panel-motif nest pack + canvas-hole sprite fill + ones-stamp period fill + path-column unroll + plus-stamp recolor + legend motif tally + motif stamp jigsaw + band concentric nest + hollow accent-fill + topology schematic + separator gap-stack + fixed-canvas + wall-tree + marker-frame + CPT + S3 + ice/DSL).
- Notebook log: `evidence/arc-prize-2026-agi-2/kernel-output/affine-arc-prize-2026-arc-agi-2.log`
- Score receipt: `evidence/arc-prize-2026-agi-2/kaggle-submissions.csv` — publicScore `0.00`.
- Local mastery reports: `reports/arc_local_20260721T131200Z/` (ice-on train **298/1076**) · overlay `reports/arc_local_20260721T162654Z/agi2/summary-overlay.json` (eval **56/172**); submit **LOCKED**.
- Contracts: [Top-score formats](Kaggle-ARC-Top-Score-Formats) · [Language Games ARC-AGI-2](Language-Games-ARC-AGI-2).
- Solver-quality lineage: `db71c28` (1/172) → `marker8_twin31` (2/172) → `s1_dimension_projection` (3/172) → `container_period_tiling` **135a2760** (4/172) → `s3_separator_ray_fill` **1ae2feb7** ×3 (7/172) → `s1_digit_separator_snake` **136b0064** (8/172) → `s1_seven_tab_merge` **20270e3b** ×2 → `s1_panel_odd_one_out` **38007db0** ×2 (12/172) → `s1_marker_frame_motif` **20a9e565** ×2 (14/172) → `s1_fixed_canvas_template` **269e22fb** ×2 → `s1_wall_tree_nested_frames` **13e47133** ×2 (18/172) → `s1_laser_mirror_beams` **142ca369** ×2 (20/172) → `s1_oriented_block_pack` **291dc1e1** ×1 (21/172) → `s1_topology_schematic` **2d0172a1** ×2 (23/172) → `s1_hollow_accent_fill` **3a25b0d8** ×2 (25/172) → `s3_separator_gap_stack` **16b78196** ×1 (26/172) → `band_concentric_nest` **45a5af55** ×1 (27/172) → `s1_panel_motif_projection` **4c7dc4dd** ×2 (29/172) → `s1_motif_stamp_jigsaw` **4e34c42c** ×2 (31/172) → `s3_period_lattice_rewrite` **16de56c4** ×2 (33/172) → `s1_legend_motif_tally` **58490d8a** ×1 (34/172) → `s3_terrain_period_bounce` **195c6913** ×2 (36/172) → `s1_solid_motif_carve` **58f5dbd5** ×1 (37/172) → `s2_plus_stamp_recolor` **1818057f** ×1 (38/172) → `s1_path_column_unroll` **7b5033c1** ×1 (39/172) → `s1_ones_stamp_period_fill` **53fb4810** ×1 (40/172) → `s1_canvas_hole_sprite_fill` **67e490f4** ×1 (41/172) → `s1_panel_motif_nest_pack` **8698868d** ×1 (42/172) → `s1_separator_block_unroll` **78332cb0** ×2 (43/172) → `s1_sep_row_extent_sort` **31f7f899** ×1 (44/172) → `s1_frame_chamber_staircase` **89565ca0** ×1 (45/172) → `s1_header_bracket_fill` **97d7923e** ×1 (46/172) → `s2_arrow_room_recolor` **21897d95** ×2 → `s2_marker_stripe_lattice` **221dfab4** ×2 (50/172) → `s2_axis_glyph_stamp` **247ef758** ×2  → `s3_box_slide_rail_fill` **271d71e2** ×1 (53/172) → `s3_staircase_interior_fill` **28a6681f** ×1 → `s2_seven_triplet_rail` **2b83f449** ×1 → `s3_cross_arm_shape_dock` **2c181942** ×1 (**56/172**).


## FoT note — 271d71e2 box-slide rail-fill (2026-07-21)

C4: BG=6; 0-bordered boxes with interiors {0,5,7}; maroon(9) near/far rails set slide axis; slide min(rail_gap, n_grey); refill by directional sweep (n_orange+steps as 7 else 5); reattach rails. Train **3/3**, eval **1/1** via `llm_llvm_bench/arc/s3_box_slide_rail_fill.py`. No Kaggle.

## FoT note — reinjection state sync 271d71e2 (2026-07-21)

Hybrid GREEN task `271d71e2` sealed **CLOSED** in
`reports/exam_reinjection/grammar/arc2/`. Mastery **53/172**. Next open
`28a6681f`. No Kaggle submit.


## FoT note — 2c181942 cross-arm shape dock (2026-07-21)

C4: BG=8; unique 4×4 four-arm cross; rotate same-color shapes to match arm connecting face; dock outward preferring longest face. Train **3/3**, eval **1/1** via `llm_llvm_bench/arc/s3_cross_arm_shape_dock.py`. No Kaggle.

## FoT note — reinjection state sync 2c181942 (2026-07-21)

Hybrid GREEN task `2c181942` sealed **CLOSED** in
`reports/exam_reinjection/grammar/arc2/`. Mastery **56/172**. Next open
`332f06d7`. No Kaggle submit.

## FoT note — 2b83f449 seven-triplet rail (2026-07-21)

C4: odd-row 777→868; even rails paint 6 at adjacent triplet-center cols; redistribute color-3 to segment edges from above-centers; suppress conflicting edge-3s across 0-boundaries. Train **2/2**, eval **1/1** via `llm_llvm_bench/arc/s2_seven_triplet_rail.py`. No Kaggle.

## FoT note — reinjection state sync 2b83f449 (2026-07-21)

Hybrid GREEN task `2b83f449` sealed **CLOSED** in
`reports/exam_reinjection/grammar/arc2/`. Mastery **55/172**. Next open
`2c181942`. No Kaggle submit.

## FoT note — 28a6681f staircase interior fill (2026-07-21)

C4: BG=0; blue(1) conserved; strip blues; Type A closed same-color L/R gaps stacked from floor; Type B open left extensions; fill A then B bottom-up until N. Train **3/3**, eval **1/1** via `llm_llvm_bench/arc/s3_staircase_interior_fill.py`. No Kaggle.

## FoT note — reinjection state sync 28a6681f (2026-07-21)

Hybrid GREEN task `28a6681f` sealed **CLOSED** in
`reports/exam_reinjection/grammar/arc2/`. Mastery **54/172**. Next open
`2b83f449`. No Kaggle submit.

## FoT note — 16b78196 separator gap-stack (2026-07-21)

C4: thick H/V separator band; objects (non-sep color) form tight high-contact vertical nest stacks (Kruskal); dock assemblies into band gaps by gap penetration then contact (V bands via transpose). Train **2/2**, eval **1/1** via `llm_llvm_bench/arc/s3_separator_gap_stack.py`. No Kaggle.

## FoT note — 3a25b0d8 hollow accent-fill (2026-07-21)

C4: 8-connected mono hollow frame + multi-color accent object; D4-align accent by frame overlap; paint accents into hollow cells; flood enclosed holes with majority accent seed. Train **2/2**, eval **2/2** via `llm_llvm_bench/arc/s1_hollow_accent_fill.py`. No Kaggle.

## FoT note — 2d0172a1 topology schematic (2026-07-21)

C4: lossy containment schematic — fg loops/leaves form a tree; draw nested frames with leaf markers by centroid side (L/R/U/D) of the medium sub-loop; outside roots attach as a 3-cell exterior bar. Train **4/4**, eval **2/2** via `llm_llvm_bench/arc/s1_topology_schematic.py`. No Kaggle.

## FoT note — 291dc1e1 oriented block pack (2026-07-21)

C4: D4-canonicalize via 0/1 and 2/8 marker strips; split 2-row bands and column-blocks; ori-conditioned vertical flip; pad to max width with 8s; stack. Train **4/4**, eval **1/1** via `llm_llvm_bench/arc/s1_oriented_block_pack.py`. No Kaggle.



## FoT note — 4c7dc4dd panel motif projection (2026-07-21)

C4: four equal hollow frames; recolor densest bichrome via template (desc→asc freq), else ortho-connect singleton anchor→ink, else XOR mono panels painted with rarest panel color. Train **2/2**, eval **2/2** via `llm_llvm_bench/arc/s1_panel_motif_projection.py`. No Kaggle.

## FoT note — 4e34c42c motif stamp jigsaw (2026-07-21)

C4: majority bg; 4-connected non-bg stamps; drop exact subarray stamps; assemble by consistent 2D overlap (`min_ov=3`); maximize pairwise overlap then minimize bbox; fill gaps with bg. Train **2/2**, eval **2/2** via `llm_llvm_bench/arc/s1_motif_stamp_jigsaw.py`. No Kaggle.


## FoT note — 16de56c4 period lattice rewrite (2026-07-21)

C4: same-shape rewrite; axis = denser multi-seed lines (rows vs cols); mono seeds → full gcd-lattice; pattern+singleton → recolor lattice in seed span if singleton on-lattice, else extend pattern and keep singleton. Train **3/3**, eval **2/2** via `llm_llvm_bench/arc/s3_period_lattice_rewrite.py`. No Kaggle.



## FoT note — 31f7f899 sep-row extent sort (2026-07-21)

C4: bg=8; separator = row with most 6s; motif cols = sep cells ∉ {8,6}; sort per-col vertical extents ascending and reassign left→right; paint sep colors clipped to input motif row bbox. Train **3/3**, eval **1/1** via `llm_llvm_bench/arc/s1_sep_row_extent_sort.py`. No Kaggle.

## FoT note — 97d7923e header-bracket fill (2026-07-21)

C4: row-0 legend colors select F–C+–F vertical brackets (mid cells touch only 0/C/F); same-col or 0-reachable pool with sole→rightmost / first→leftmost / last→rightmost / mid→nearest; recolor mid C→F. Train **3/3**, eval **1/1** via `llm_llvm_bench/arc/s1_header_bracket_fill.py`. No Kaggle.

## FoT note — reinjection state sync 97d7923e (2026-07-21)

Hybrid GREEN task `97d7923e` sealed **CLOSED** in
`reports/exam_reinjection/grammar/arc2/`. Mastery **46/172**. Next open was `21897d95` (now CLOSED). No Kaggle submit.

## FoT note — 21897d95 arrow-room recolor (2026-07-21)

C4: T-shaped color-1 arrows (payload = non-1 bar-center else source room) recolor the
stem-neighbor room; square grids remap in place; non-square expand block grid then
rotate 90°. Train **4/4**, eval **2/2** via `llm_llvm_bench/arc/s2_arrow_room_recolor.py`.
No Kaggle.

## FoT note — reinjection state sync 21897d95 (2026-07-21)

Hybrid GREEN task `21897d95` sealed **CLOSED** in
`reports/exam_reinjection/grammar/arc2/`. Mastery **48/172**. Next open
from reinjection miss queue. No Kaggle submit.

## FoT note — 221dfab4 marker-stripe lattice (2026-07-21)

C4: color-4 marker stripe (H/V); on marker-parity lattice paint cycle [4,4,3]
by half-step distance — 4 fills stripe, 3 paints stripe∪foreground, off-parity
stripe clears to majority bg. Train **2/2**, eval **2/2** via
`llm_llvm_bench/arc/s2_marker_stripe_lattice.py`. No Kaggle.

## FoT note — reinjection state sync 221dfab4 (2026-07-21)

Hybrid GREEN task `221dfab4` sealed **CLOSED** in
`reports/exam_reinjection/grammar/arc2/`. Mastery **54/172**. Next open
from reinjection miss queue. No Kaggle submit.

## FoT note — 247ef758 axis-glyph stamp (2026-07-21)

C4: solid nonzero axis column; left glyphs of color C clear and stamp centered
copies at every (right-col C row × top-row C col) marker pair. Train **3/3**,
eval **2/2** via `llm_llvm_bench/arc/s2_axis_glyph_stamp.py`. No Kaggle.

## FoT note — reinjection state sync 247ef758 (2026-07-21)

Hybrid GREEN task `247ef758` sealed **CLOSED** in
`reports/exam_reinjection/grammar/arc2/`. Mastery **54/172**. Next open
from reinjection miss queue. No Kaggle submit.

## FoT note — 89565ca0 frame-chamber staircase (2026-07-21)

C4: marker = most-component scatter color; each other non-bg color is a frame/cage; chamber count from closed-border rooms (object + touching-marker walls, seal near-full dividers thr=0.7, drop size-1 pockets); emit staircase `color*chambers + marker*(W-chambers)` sorted by chambers. Train **3/3**, eval **1/1** via `llm_llvm_bench/arc/s1_frame_chamber_staircase.py`. No Kaggle.

## FoT note — reinjection state sync 89565ca0 (2026-07-21)

Hybrid GREEN task `89565ca0` sealed **CLOSED** in
`reports/exam_reinjection/grammar/arc2/`. Mastery **45/172** (superseded by header-bracket fill). Next open
`21897d95` (S4_REINJECT). No Kaggle submit.

## FoT note — 78332cb0 separator-block unroll (2026-07-21)

C4: separator color partitions equal blocks; 1D swap/parity pack; 2D diagonal order with motif-count branch (multi→vertical, mono→swap+horizontal). Train **3/3**, eval **2/2** via `llm_llvm_bench/arc/s1_separator_block_unroll.py`. No Kaggle.

## FoT note — reinjection state sync 78332cb0 (2026-07-21)

Hybrid GREEN task `78332cb0` sealed **CLOSED** in
`reports/exam_reinjection/grammar/arc2/`. Mastery **43/172** (superseded by sep-row extent sort). Next open
`21897d95` (S4_REINJECT). No Kaggle submit.

## FoT note — 8698868d panel-motif nest pack (2026-07-21)

C4: two object sizes (panels/motifs); pair by panel bg-cell count = motif 4-conn bg-hole component count; solidify+center-stamp; arrange on panel bbox lattice. Train **2/2**, eval **1/1** via `llm_llvm_bench/arc/s1_panel_motif_nest_pack.py`. No Kaggle.

## FoT note — reinjection state sync 8698868d (2026-07-21)

Hybrid GREEN task `8698868d` sealed **CLOSED** in
`reports/exam_reinjection/grammar/arc2/`. Mastery **42/172** (superseded by separator-block unroll). Next open
`21897d95` (S4_REINJECT). No Kaggle submit.

## FoT note — 67e490f4 canvas-hole sprite fill (2026-07-21)

C4: majority bg; largest non-bg component = canvas crop; holes filled by majority sprite color per mask class (rotation+mirror). Train **2/2**, eval **1/1** via `llm_llvm_bench/arc/s1_canvas_hole_sprite_fill.py`. No Kaggle.

## FoT note — reinjection state sync 67e490f4 (2026-07-21)

Hybrid GREEN task `67e490f4` sealed **CLOSED** in
`reports/exam_reinjection/grammar/arc2/`. Mastery **41/172** (superseded by nest pack seal). Next open
`21897d95` (S4_REINJECT). No Kaggle submit.

## FoT note — 53fb4810 ones-stamp period fill (2026-07-21)

C4: majority bg; color-1 anchors; contiguous non-bg stamp on one side; tile that period on the opposite side of the stamp into non-1 cells. Train **2/2**, eval **1/1** via `llm_llvm_bench/arc/s1_ones_stamp_period_fill.py`. No Kaggle.

## FoT note — reinjection state sync 53fb4810 (2026-07-21)

Hybrid GREEN task `53fb4810` sealed **CLOSED** in
`reports/exam_reinjection/grammar/arc2/`. Mastery **40/172**. Next open
`21897d95` (S4_REINJECT). No Kaggle submit.

## FoT note — 21897d95 honest S4 REINJECT (2026-07-21)

Oriented color-1 digit stamps (U/D/L/R) plus singleton 1s observed across 4 trains; outputs drop 1 and reshape. No train-exact C4 locked this cycle — status **REINJECT** at
`reports/exam_reinjection/grammar/arc2/s2_21897d95_reinject.json`. Parallel CLOSED `53fb4810`. No Kaggle.

## FoT note — 7b5033c1 path-column unroll (2026-07-21)

C4: majority bg; non-bg cells form a simple 4-path (2 endpoints); walk from lex-smallest endpoint; emit N×1 color column. Train **2/2**, eval **1/1** via `llm_llvm_bench/arc/s1_path_column_unroll.py`. No Kaggle.

## FoT note — reinjection state sync 7b5033c1 (2026-07-21)

Hybrid GREEN task `7b5033c1` sealed **CLOSED** in
`reports/exam_reinjection/grammar/arc2/`. Mastery **39/172**. Next open
`21897d95`. No Kaggle submit.

## FoT note — 1818057f plus-stamp recolor (2026-07-21)

C4: bipartite palette; every orthogonal plus of 5 foreground cells recolors to 8. Train **3/3**, eval **1/1** via `llm_llvm_bench/arc/s2_plus_stamp_recolor.py`. No Kaggle.

## FoT note — reinjection state sync 1818057f (2026-07-21)

Hybrid GREEN task `1818057f` sealed **CLOSED** in
`reports/exam_reinjection/grammar/arc2/`. Mastery **38/172**. Next open
`21897d95`. No Kaggle submit.

## FoT note — 58f5dbd5 solid-motif carve (2026-07-21)

C4: majority bg; solid filled rects; non-solid C-cells form motif; punch motif into solid interior (invert stamp); crop solids+frame. Train **3/3**, eval **1/1** via `llm_llvm_bench/arc/s1_solid_motif_carve.py`. No Kaggle.

## FoT note — reinjection state sync 58f5dbd5 (2026-07-21)

Hybrid GREEN task `58f5dbd5` sealed **CLOSED** in
`reports/exam_reinjection/grammar/arc2/`. Mastery **37/172**. Next open
`ar25`. No Kaggle submit.

## FoT note — 195c6913 terrain period-bounce (2026-07-21)

C4: dual terrain; top-row 2×2 stamps = period P; remaining stamp = M; erase seeds; from left-edge seeds bounce East↔North painting P, place M on object hits; stop on OOB or blocked facing. Train **3/3**, eval **2/2** via `llm_llvm_bench/arc/s3_terrain_period_bounce.py`. No Kaggle.

## FoT note — reinjection state sync 195c6913 (2026-07-21)

Hybrid GREEN task `195c6913` sealed **CLOSED** in
`reports/exam_reinjection/grammar/arc2/`. Mastery **37/172**. Next open
`58f5dbd5`. No Kaggle submit.

## FoT note — 58490d8a legend motif tally (2026-07-21)

C4: majority bg; largest mostly-zero panel is the legend; unique marker colors on that crop; count 8-connected motifs of each marker in the main canvas (legend masked); emit legend-shaped tally with `count` spaced copies per marker row. Train **3/3**, eval **1/1** via `llm_llvm_bench/arc/s1_legend_motif_tally.py`. No Kaggle.


## FoT note — 58490d8a zero-panel motif-count (2026-07-21)

C4: majority wall; output = bbox of 0-cells; each panel marker color C paints period-2 along its row once per 8-connected outside C-motif. Train **3/3**, eval **1/1** via `llm_llvm_bench/arc/s1_zero_panel_motif_count.py`. No Kaggle.

## FoT note — reinjection state sync (2026-07-21)

Hybrid GREEN task `58490d8a` sealed **CLOSED** in
`reports/exam_reinjection/grammar/arc2/`. Mastery **34/172**. Next open
`195c6913`. No Kaggle submit.


## FoT note — 45a5af55 band concentric nest (2026-07-21)

C4: full-width uniform row bands nest as concentric square frames; last band fills center; `size = 2*sum(t[:-1]) + t[-1]`. Train **2/2**, eval **1/1** via `band_concentric_nest` in `llm_llvm_bench/arc/s1_dimension_projection.py`. No Kaggle.

## FoT note — 142ca369 laser-mirror beams (2026-07-21)

C4 locked via `llm_llvm_bench/arc/s1_laser_mirror_beams.py`. Train **3/3**, labeled eval **2/2**. No Kaggle.

## FoT note — 269e22fb fixed-canvas template (2026-07-21)

C4: every demo output is one D4 orientation (optional bit-invert) of a single 20×20 binary template, recolored to the input's two colors. Input is an exact crop of that oriented template. Train **5/5**, eval **2/2** via `llm_llvm_bench/arc/s1_fixed_canvas_template.py`. No Kaggle.

## FoT note — 13e47133 wall-tree nested frames (2026-07-21)

S3 spatial rewrite CLOSED. C4: full-height/width separators form a wall tree; rooms get Chebyshev depth rings colored by seeded period. Train **3/3**, eval **2/2** via `llm_llvm_bench/arc/s1_wall_tree_nested_frames.py`. No Kaggle.

## FoT note — 20a9e565 marker-frame motif (2026-07-21)

OPEN_REINJECT stub closed. C4: color-5 corner markers define the output frame; remaining nonzero cells are a size-progression of self-similar motifs (comb / chevron / ladder / ribbon / bracket). Extrapolate along the spatial AP with the family generator; crop the marker frame. Train replay **3/3**, labeled eval **2/2** via `llm_llvm_bench/arc/s1_marker_frame_motif.py`. No Kaggle submit.

## FoT note — 135a2760 container period tiling (2026-07-21)

Prior live C4 (“horizontal reflection of color 1 inside color-3 bbox”) was **REINJECT**’d: train[1] repairs colors `{1,3,4,8,9}`, not color-1-only. Corrected C4 locked after demonstration replay **2/2** and labeled eval **1/1** via `llm_llvm_bench/arc/container_period_tiling.py`. No Kaggle submit.

## FoT note — 1ae2feb7 separator ray-fill (2026-07-21)

S3 `separator_ray_fill` closed: train **3/3**, labeled eval **3/3** via
`llm_llvm_bench/arc/s3_separator_ray_fill.py`. Vertical uniform separator;
content-side motifs ray-fill empty side; leftward phase = reversed rightward
buffer. No Kaggle submit.

## FoT note — 136b0064 digit-separator snake (2026-07-21)

Franklin slice candidates (7-col vertical crop) **REINJECT**’d — fail train
replay. Correct C4 locked: port-chained digit glyph snake on a 7-wide canvas
(`s1_digit_separator_snake`, solver SHA `9070588`). Train **3/3**, labeled eval
**1/1**; mastery **8/172**. UI capture:
`reports/arc_ui_audit_s1_20260721T134500Z/136b0064_input.ppm`. No Kaggle submit.

## 2026-07-21 local quality pass

The local replay-gated DSL now composes a geometry operation with a learned
color permutation, derives uniform scale/tile/reduce operations from training
dimensions, selects color or foreground connected-component crops, and tests
four gravity directions. Every candidate must reproduce every demonstration
before it can populate either answer slot.

This lifted the labeled training receipt from **12/1076** exact grids to
**19/1076** and licensed tasks from **13** to **20**. The held-out evaluation
receipt remains **0/172**; the requested eval lift was not observed, so quality
is recorded as **0/172**, not represented as a mastery win. The top-score JSON
and parquet validators stayed GREEN throughout. No new ARC exam UI surface
appeared, so the existing UI receipts remain current.

## 2026-07-21 held-out structural pass

Main commit: `7ab6e05` (`feat(arc): expand replay-gated structural DSL`).

The replay-gated DSL now also tests separator-line removal, left/right and
top/bottom reflection, background-preserving symmetry completion, and isolated
single-color components. Color fitting now composes after these object
selection rules as well as after geometry.

This increased the training receipt to **22/1076** exact grids and **24/1000**
licensed tasks. It did **not** license an evaluation task: evaluation remains
**0/172** at that SHA. Report: `reports/arc_local_20260721T105900Z/`.

## 2026-07-21 MIT arc-icecuber hybrid (eval > 0)

Vendored MIT [ARC-icecuber](https://github.com/victorvikram/ARC-icecuber) under
`harnesses/arc-icecuber` with a macOS/local adapter
(`llm_llvm_bench/arc/icecuber_adapter.py`). Hybrid mastery scores against
official evaluation/training solutions files (scoring contract verified).

Receipt: `reports/arc_local_20260721T110813Z/` — overall **GREEN**.

| Metric | Value |
| --- | --- |
| Eval exact | **8/172** (`981571dc` ice + `0934a4d8` marker8 + `2ba387bc` S1 pack + `135a2760` CPT + `1ae2feb7` S3×3 + `136b0064` snake) |
| Train exact | **298/1076** (icecuber 296 + DSL unique) |
| Failure analyses | full miss taxonomy with S1/S2/S3 classes |
| Submit | **LOCKED** — no Kaggle submit |

## Path forward

1. Keep `NO_KAGGLE_SUBMIT.lock`.
2. Own remaining **S1 dimension projection** then **S3 spatial rewrite**.
3. Re-run `./bin/run-arc-local-mastery.sh`; schema must stay green.
4. Steward re-opens submit only after explicit `ALLOW_KAGGLE_SUBMIT=1` at high local confidence (≥95%+ labeled eval).
