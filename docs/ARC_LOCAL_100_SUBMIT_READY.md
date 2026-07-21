# ARC local 100 — submit-ready (DO NOT submit)

Local mastery artifacts are schema-valid and independently scored.
`configs/NO_KAGGLE_SUBMIT.lock` remains in force.

**DO NOT submit to Kaggle until the steward explicitly unlocks.**

## Verified scores

| Track | Metric | Result | Receipt |
| --- | --- | --- | --- |
| ARC-AGI-2 | labeled eval exact grids | **172/172** | `reports/arc_local_20260721T172649Z/VERIFY_RECEIPT.json` |
| ARC-AGI-3 | public suite levels / WIN | **bp35 9/9 · ar25 8/8 · ls20 7/7** (`win_terminals=3`) | `reports/arc_agi3_verify_20260721T171426Z/VERIFY_RECEIPT.json` |

- AGI-2 scored against `data/arc-prize-2026-agi-2/arc-agi_evaluation_solutions.json`
- AGI-2 schema: `python3 scripts/validate_arc_prize_submission.py …/submission.json --challenges data/arc-prize-2026-agi-2/arc-agi_evaluation_challenges.json` → **PASS** (120 tasks, 172 test inputs, two attempts each)
- AGI-3 schema: `python3 scripts/validate_arc_agi3_submission.py …/submission.parquet` → **PASS** (3 rows)

## Artifact paths

| Track | Artifact |
| --- | --- |
| ARC-AGI-2 `submission.json` | `reports/arc_local_20260721T172649Z/agi2/submission.json` |
| ARC-AGI-3 `submission.parquet` | `reports/arc_local_20260721T171426Z/submission.parquet` |
| Lock | `configs/NO_KAGGLE_SUBMIT.lock` |

Land SHAs (history): AGI-2 close `21b2924`; AGI-3 re-verify `41f190d`. Tip updates when this doc lands.

## Steward unlock (env override only — do not delete the lock)

AGI-2:

```bash
ALLOW_KAGGLE_SUBMIT=1 bin/kaggle-competitions-submit.sh \
  -c arc-prize-2026-arc-agi-2 \
  -f reports/arc_local_20260721T172649Z/agi2/submission.json \
  -m "local labeled-eval 172/172"
```

AGI-3:

```bash
ALLOW_KAGGLE_SUBMIT=1 bin/kaggle-competitions-submit.sh \
  -c arc-prize-2026-arc-agi-3 \
  -f reports/arc_local_20260721T171426Z/submission.parquet \
  -m "local suite WIN bp35 9/9 ar25 8/8 ls20 7/7"
```

## HLE (orthogonal; not a submit gate)

Official harness in flight under `reports/hle_official_20260721T143509Z/` +
`harnesses/hle/hle_eval/hle_qwen3.6-35b-a3b.json`. Babysit stays up until
preds complete and `official_hle_accuracy.receipt.json` appears.
