# ARC Prize 2026 (ARC-AGI-2) — Kaggle live record

Official competition: [ARC Prize 2026 — ARC-AGI-2](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-2)

**Submit status:** **BLOCKED** — `configs/NO_KAGGLE_SUBMIT.lock`. No new Kaggle submits until local mastery is green **and** the steward sets `ALLOW_KAGGLE_SUBMIT=1`.

## LOCAL mastery gate (required before any future submit)

| Gate | Result |
|:---|:---|
| Language-game doctrine | [Language-Games-ARC-AGI-2](Language-Games-ARC-AGI-2) · hub [Exam Invariants](Language-Games-Exam-Invariants) (`f983986`) |
| Top-score format study | [Kaggle-ARC-Top-Score-Formats](Kaggle-ARC-Top-Score-Formats) (`a04e483`) |
| Hard schema validator | `scripts/validate_arc_prize_submission.py` on fixture + official sample + local `submission.json` vs test challenges |
| Local harness | `bin/run-arc-local-mastery.sh` → **overall GREEN** (schema/hard gates) |
| Eval quality (local) | **0/172** exact grids on evaluation solutions (transform baseline) |
| Train licensed | **13/1000** tasks with training-consistent hypotheses; **12/1076** grids |
| Public probe | publicScore **0.00** = **PROCESS_PROBE** (premature process test) |
| LB contrast | Top public ~**65.83** — format≠mastery |

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
- Offline evaluation set: 0/172 exact grids for this initial transformation baseline.
- Notebook log: `evidence/arc-prize-2026-agi-2/kernel-output/affine-arc-prize-2026-arc-agi-2.log`
- Score receipt: `evidence/arc-prize-2026-agi-2/kaggle-submissions.csv` — publicScore `0.00`.
- Local mastery report: `reports/arc_local_*/summary.json` (validators GREEN; quality RED).

## Path forward

1. Keep `NO_KAGGLE_SUBMIT.lock`.
2. Grow licensed demonstration-replay transforms (close local eval 0/172 toward mastery).
3. Re-run `./bin/run-arc-local-mastery.sh` until quality metrics move; schema must stay green.
4. Steward re-opens submit only after explicit `ALLOW_KAGGLE_SUBMIT=1`.
