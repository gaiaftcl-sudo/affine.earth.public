# ARC-AGI-2 — local 100% mastery → submit-ready (LOCKED)

**Mastery SHA:** `21b2924`  
**Verified labeled eval:** **172/172** exact grids  
**Artifact:** `reports/arc_local_20260721T172649Z/agi2/submission.json` — **120 keys / 172 grids** (schema PASS; not under-coverage)  
**Kaggle direct CLI:** **BLOCKED** — competitions are **Notebooks-only** (steward unlock proved HTTP 400). See `docs/ARC_LOCAL_100_SUBMIT_READY.md`.  
**Lock:** `configs/NO_KAGGLE_SUBMIT.lock` stays on.  
**HLE babysit:** leave running (`reports/hle_official_20260721T143509Z/`).

## 120 vs 172 — not under-coverage

| Number | Meaning | Set |
|:---|:---|:---|
| **120** | `submission.json` **task keys** (`task_id` → attempts) | labeled **evaluation** challenges |
| **172** | **test grids** (sum of per-task `test` inputs; each has `attempt_1` + `attempt_2`) | same evaluation set |
| **0** | missing evaluation `task_id`s | — |

So “schema green, 120/172” means: validator saw **120 tasks** covering **172 test inputs**. That is full labeled-eval coverage, not a hole.

## Two different JSON sets (do not mix)

| Artifact role | Challenges file | Keys | Grids | Path |
|:---|:---|:---|:---|:---|
| **Mastery / FoT** (labels exist) | `arc-agi_evaluation_challenges.json` | **120** | **172** | `reports/arc_local_20260721T172649Z/agi2/local-evaluation-submission.json` (also copied as `submission.json`) |
| **Kaggle contract** (held-out; no public labels) | `arc-agi_test_challenges.json` | **240** | **259** | emitted by air-gapped kernel under `kaggle/arc-prize-2026-agi-2/` |

## Direct CLI — BLOCKED

Do **not** run `bin/kaggle-competitions-submit.sh`. Kaggle returned **400** Notebooks-only + daily quota (1). Quota ≈ reset **2026-07-21T23:57Z**. No new submit until notebook ready + reset.

## Steward path — air-gapped notebook

| Track | Package |
|:---|:---|
| AGI-2 | `kaggle/arc-prize-2026-agi-2/` (`arc_agi_2_kaggle.py`) |
| AGI-3 | `kaggle/arc-prize-2026/` (`arc_prize_kaggle.py`) |

```bash
# After UTC quota reset only — push kernel, then Submit from Kaggle Notebook UI
ALLOW_KAGGLE_SUBMIT=1 bin/run-arc-prize-kaggle.sh --push-notebook
ALLOW_KAGGLE_SUBMIT=1 kaggle kernels push -p kaggle/arc-prize-2026-agi-2
```

`notebooks/` submit pack not landed yet (agent may be in flight).

## Status snapshot

| Gate | State |
|:---|:---|
| Labeled eval exact | **172/172** @ `21b2924` |
| Eval submission keys/grids | **120 / 172** (complete) |
| `NO_KAGGLE_SUBMIT.lock` | **PRESENT** |
| Direct `kaggle-competitions-submit.sh` | **BLOCKED** (Notebooks-only) |
| Next path | Air-gapped notebook after quota reset |

No Kaggle submit from this document.
