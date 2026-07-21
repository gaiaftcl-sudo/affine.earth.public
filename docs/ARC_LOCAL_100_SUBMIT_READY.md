# ARC local 100 — submit-ready (DO NOT submit)

Local mastery artifacts are schema-valid and independently scored.
`configs/NO_KAGGLE_SUBMIT.lock` remains in force.

**DO NOT submit to Kaggle until the steward explicitly says to unlock.**
Agents must not remove the lock file. Env override only when steward orders it.

## Verified scores

| Track | Metric | Result | Receipt |
| --- | --- | --- | --- |
| ARC-AGI-2 | labeled eval exact grids | **172/172** | `reports/arc_local_20260721T172649Z/VERIFY_RECEIPT.json` · `reports/exam_reinjection/agi2_172_verify.json` |
| ARC-AGI-2 reinjection | grammar CLOSED | **120/120** | tip close-loop `95d7b89` |
| ARC-AGI-3 | public suite levels / WIN | **bp35 9/9 · ar25 8/8 · ls20 7/7** (`win_terminals=3`) | `reports/arc_agi3_verify_20260721T171426Z/VERIFY_RECEIPT.json` · `reports/arc_local_20260721T171426Z/README.md` |

- AGI-2 scored against `data/arc-prize-2026-agi-2/arc-agi_evaluation_solutions.json` → **172/172**, `misses=[]`
- AGI-2 schema: `scripts/validate_arc_prize_submission.py` vs evaluation challenges → **PASS** (120 tasks / 172 test inputs, two attempts each)
- AGI-3 schema: `scripts/validate_arc_agi3_submission.py` → **PASS** (3 rows; scores 9/8/7; `end_of_game=true`)

## Artifact paths

| Track | Artifact | SHA-256 |
| --- | --- | --- |
| ARC-AGI-2 `submission.json` | `reports/arc_local_20260721T172649Z/agi2/submission.json` | `3e27792b45d4f186ca436d042841c7db5a7164e71a4a018da1b01a894719e082` |
| ARC-AGI-3 `submission.parquet` | `reports/arc_local_20260721T171426Z/submission.parquet` | `9ffc90cee088b086e5d2539abee76b77346191666a657dd63dbf3cf0de340c73` |
| Lock | `configs/NO_KAGGLE_SUBMIT.lock` | `f22461e650b7dd6e112313df6806205462c1809d45b906d9711971c04785317f` |

## Git SHAs

| Role | SHA |
| --- | --- |
| Tip (this seal) | see `git rev-parse HEAD` after this commit |
| AGI-2 independent verify receipt | `6d3a705` (`reports/arc_local_20260721T172649Z/VERIFY_RECEIPT.json`) |
| AGI-2 land (172/172 COMPLETE) | `21b2924` |
| Reinjection CLOSED 120/120 + bp35 9/9 | `95d7b89` |
| AGI-3 independent triad re-verify | `41f190d` |
| AGI-3 FoT + steward unlock one-liner | `6d3a705` |

## Steward unlock (env override only — do not delete the lock)

One-liner pattern (steward only):

```bash
ALLOW_KAGGLE_SUBMIT=1 bin/kaggle-competitions-submit.sh \
  -c <competition> -f <artifact> -m "<message>"
```

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

Without `ALLOW_KAGGLE_SUBMIT=1`, `bin/kaggle-submit-guard.sh` exits 99.

## Steward unlock attempt (2026-07-21T17:39Z)

`ALLOW_KAGGLE_SUBMIT=1` authorized; lock **kept**. Both tracks uploaded blob then got Kaggle **400**:
daily Submission allowance (1) exhausted (~6.3h UTC) **and** competitions accept **Notebooks only**.
No new refs. Standing: AGI-2 **54875115** / **0.00**; AGI-3 **54875048** / **0.12**.
Receipts: `reports/kaggle_submit_20260721T173500Z/`.

## HLE (orthogonal; not a submit gate)

Official harness **still running**: `reports/hle_official_20260721T143509Z/`
— live preds **690/2500** (`harnesses/hle/hle_eval/hle_qwen3.6-35b-a3b.json`); `acc=null` until judge finishes.
Accuracy written only when preds finish and `official_hle_accuracy.receipt.json` appears.
