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
| Eval quality (local) | **7/172** exact grids (marker8 + S1 pack + CPT + S3 ray-fill + ice/DSL; was **4/172**) |
| Train quality (local) | **298/1076** exact grids (ice-on receipt); **24/1000** DSL-licensed tasks |
| Engine | `LOCAL_HYBRID_SOLVER` = marker8_twin31 + s1_dimension_projection + container_period_tiling + s3_separator_ray_fill + icecuber + DSL |
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
- Offline evaluation set: **7/172** exact grids (marker8 + S1 + CPT + S3 ray-fill + ice/DSL).
- Notebook log: `evidence/arc-prize-2026-agi-2/kernel-output/affine-arc-prize-2026-arc-agi-2.log`
- Score receipt: `evidence/arc-prize-2026-agi-2/kaggle-submissions.csv` — publicScore `0.00`.
- Local mastery reports: `reports/arc_local_20260721T131200Z/` (ice-on train **298/1076**) · overlay `reports/arc_local_20260721T135000Z/agi2/summary-overlay.json` (eval **7/172**); submit **LOCKED**.
- Contracts: [Top-score formats](Kaggle-ARC-Top-Score-Formats) · [Language Games ARC-AGI-2](Language-Games-ARC-AGI-2).
- Solver-quality lineage: `db71c28` (1/172) → `marker8_twin31` (2/172) → `s1_dimension_projection` (3/172) → `container_period_tiling` **135a2760** (4/172) → `s3_separator_ray_fill` **1ae2feb7** ×3 (**7/172**).

## FoT note — 135a2760 container period tiling (2026-07-21)

Prior live C4 (“horizontal reflection of color 1 inside color-3 bbox”) was **REINJECT**’d: train[1] repairs colors `{1,3,4,8,9}`, not color-1-only. Corrected C4 locked after demonstration replay **2/2** and labeled eval **1/1** via `llm_llvm_bench/arc/container_period_tiling.py`. No Kaggle submit.

## FoT note — 1ae2feb7 separator ray-fill (2026-07-21)

S3 `separator_ray_fill` closed: train **3/3**, labeled eval **3/3** via
`llm_llvm_bench/arc/s3_separator_ray_fill.py`. Vertical uniform separator;
content-side motifs ray-fill empty side; leftward phase = reversed rightward
buffer. No Kaggle submit.

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
| Eval exact | **7/172** (`981571dc` ice + `0934a4d8` marker8 + `2ba387bc` S1 pack + `135a2760` CPT + `1ae2feb7` S3×3) |
| Train exact | **298/1076** (icecuber 296 + DSL unique) |
| Failure analyses | full miss taxonomy with S1/S2/S3 classes |
| Submit | **LOCKED** — no Kaggle submit |

## Path forward

1. Keep `NO_KAGGLE_SUBMIT.lock`.
2. Own remaining **S1 dimension projection** then **S3 spatial rewrite**.
3. Re-run `./bin/run-arc-local-mastery.sh`; schema must stay green.
4. Steward re-opens submit only after explicit `ALLOW_KAGGLE_SUBMIT=1` at high local confidence (≥95%+ labeled eval).
