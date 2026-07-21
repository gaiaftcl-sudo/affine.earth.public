# ARC local 100 — submit-ready (DO NOT CLI-submit)


**Live licensed fill:** `68/259` (26.25%) · identity `191` · experience-path ON · NOT submit-ready until ≥95%+.
Local mastery artifacts are schema-valid and independently scored.
`configs/NO_KAGGLE_SUBMIT.lock` remains in force.

**DO NOT** `kaggle competitions submit` until steward unlocks **and** UTC daily
quota has reset **and** air-gapped kernels have been pushed + Submitted from
the Notebook UI. Agents must not remove the lock file.

## Official rule sources

| Track | Platform | Rules / data |
| --- | --- | --- |
| ARC-AGI-2 | Kaggle `arc-prize-2026-arc-agi-2` | [Overview](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-2) · [Data](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-2/data) · local mirror `data/arc-prize-2026-agi-2/` |
| ARC-AGI-3 | Kaggle `arc-prize-2026-arc-agi-3` | [Overview](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3) · [Data](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/data) · local mirror `data/arc-prize-2026/` |
| HLE | HF `cais/hle` (not Kaggle) | [agi.safe.ai](https://agi.safe.ai/) · [CAIS evaluator](https://github.com/centerforaisafety/hle) · gated dataset |

Platform proof (2026-07-21T17:39Z HTTP 400 body): **Notebooks only** + **daily Submission allowance (1)**.

## RULE CHECKLIST (MUST-PASS)

| # | Rule | AGI-2 | AGI-3 | HLE |
| --- | --- | --- | --- | --- |
| R1 | Submit path = Notebook / kernel UI (not CLI file upload) | ✅ proven (CLI → 400) | ✅ proven (CLI → 400) | ✅ N/A (HF judge) |
| R2 | Internet disabled in kernel metadata | ✅ `enable_internet=false` | ✅ `enable_internet=false` | N/A |
| R3 | Daily quota ≤ 1 submission / team / day (UTC) | ✅ blocked until ≈ **2026-07-21T23:57Z** | ✅ same | N/A |
| R4 | Output filename exact | ✅ `submission.json` | ✅ `submission.parquet` | preds JSON + judge |
| R5 | Schema / shape | ✅ **240/240** tasks · **259/259** grids · `attempt_1`/`attempt_2` | ✅ cols `row_id,game_id,end_of_game,score` | CAIS harness format |
| R6 | **Licensed fill** `attempt_1 ≠ test input` | ❌ **68/259 (26.25%)** — identity 191 = **FAIL for 100%** | ✅ triad WIN | preds in flight |
| R7 | No junk-submit against exhausted quota | ✅ lock + no CLI | ✅ lock + no CLI | leave predict alive |
| R8 | Team / late-submit | follow Kaggle competition rules page at submit time | same | HF terms + CAIS judge only |
| R9 | Identity fill ≠ mastery | ❌ **FAIL** — copying test input into `attempt_1` is schema-legal but **not** a 100% license | N/A | N/A |

### Licensed gate (AGI-2 platform) — MEASURED

| Metric | Value | Verdict |
| --- | --- | --- |
| Shape | 240 tasks / 259 grids | ✅ schema PASS |
| Licensed (`attempt_1 ≠ test input`) | **68/259 (26.25%)** | ❌ FAIL for 100% | ❌ FAIL for 100% | ❌ FAIL for 100% |
| Identity `attempt_1` | **213/259** | ❌ not mastery |
| FoT labeled-eval (disjoint) | **172/172** | ✅ local only — not private test |
| Hybrid licensed-fill | `reports/airgap_agi2_test_20260721T175400Z/` (parallel, ice timeout 45s) | in flight — **no submit** |

**Do not claim AGI-2 100% until licensed = 259/259.** Shape 259/259 alone is insufficient.

### Honest mastery ≠ Kaggle private score

| Fact | Value |
| --- | --- |
| Local AGI-2 mastery | **172/172** vs `arc-agi_evaluation_*` (120 tasks) |
| Competition-shaped AGI-2 input | `arc-agi_test_challenges.json` = **240 tasks / 259 grids** (disjoint from eval) |
| Overlap eval ∩ test | **0** task IDs |
| Conclusion | Local 172/172 does **not** auto-score 100% on Kaggle private test. Notebook must regenerate from mounted competition input (or a solver that covers private tasks). |

## Verified local scores

| Track | Metric | Result | Receipt |
| --- | --- | --- | --- |
| ARC-AGI-2 | labeled eval exact grids | **172/172** | `reports/arc_local_20260721T172649Z/VERIFY_RECEIPT.json` |
| ARC-AGI-2 reinjection | grammar CLOSED | **120/120** | tip close-loop |
| ARC-AGI-3 | public suite levels / WIN | **bp35 9/9 · ar25 8/8 · ls20 7/7** | `reports/arc_agi3_verify_20260721T171426Z/VERIFY_RECEIPT.json` |

- AGI-2 schema vs evaluation challenges → **PASS** (120 / 172)
- AGI-2 schema vs test challenges on dry-run regenerate → **PASS** (240 / 259)
- AGI-3 schema → **PASS** (3 rows; scores 9/8/7; `end_of_game=true`)

## Artifact paths

| Track | Artifact | SHA-256 |
| --- | --- | --- |
| ARC-AGI-2 `submission.json` (eval mastery) | `reports/arc_local_20260721T172649Z/agi2/submission.json` | `3e27792b45d4f186ca436d042841c7db5a7164e71a4a018da1b01a894719e082` |
| ARC-AGI-3 `submission.parquet` | `reports/arc_local_20260721T171426Z/submission.parquet` | `9ffc90cee088b086e5d2539abee76b77346191666a657dd63dbf3cf0de340c73` |
| Lock | `configs/NO_KAGGLE_SUBMIT.lock` | `f22461e650b7dd6e112313df6806205462c1809d45b906d9711971c04785317f` |

## Notebook packages (air-gapped)

| Track | Package | Entry | Competition source |
| --- | --- | --- | --- |
| ARC-AGI-2 | `kaggle/arc-prize-2026-agi-2/` | `arc_agi_2_kaggle.py` + `kernel-metadata.json` | `arc-prize-2026-arc-agi-2` |
| ARC-AGI-3 | `kaggle/arc-prize-2026/` | `arc_prize_kaggle.py` + `kernel-metadata.json` | `arc-prize-2026-arc-agi-3` |

Local dry-run (no submit):

```bash
bin/prepare-kaggle-notebook-submit.sh --dry-run-only
```

## Direct CLI submit — BLOCKED (Notebooks-only)

**Do not use** `bin/kaggle-competitions-submit.sh`.

Steward unlock with `ALLOW_KAGGLE_SUBMIT=1` (2026-07-21T17:39Z) proved both tracks return Kaggle **HTTP 400**:

> Submission not allowed: Your team has used its daily Submission allowance (1) today… **This competition only accepts Submissions from Notebooks.**

| Track | Competition | Direct CLI |
| --- | --- | --- |
| ARC-AGI-2 | `arc-prize-2026-arc-agi-2` | **BLOCKED** — Notebooks-only |
| ARC-AGI-3 | `arc-prize-2026-arc-agi-3` | **BLOCKED** — Notebooks-only |

Receipts: `reports/kaggle_submit_20260721T173500Z/`.
Standing refs (OLD probes, not mastery): AGI-2 **54875115** / **0.00**; AGI-3 **54875048** / **0.12**.

### Quota ETA

- Attempt: **2026-07-21T17:39:04Z**
- Reset ≈ **2026-07-21T23:57Z** UTC (~6.3h from attempt)
- **No new submit** until after reset **and** dry-run GREEN **and** kernel push + Notebook UI Submit

## Steward notebook submit steps (after quota reset)

```bash
# 1) Local GREEN
bin/prepare-kaggle-notebook-submit.sh --dry-run-only

# 2) Push kernels ONLY (not competitions submit)
ALLOW_KAGGLE_SUBMIT=1 bin/prepare-kaggle-notebook-submit.sh --push-kernels

# 3) Kaggle UI: Run All → verify working files → Submit from notebook
#    AGI-2 → /kaggle/working/submission.json
#    AGI-3 → /kaggle/working/submission.parquet
```

Without `ALLOW_KAGGLE_SUBMIT=1`, push exits 99. Lock stays.

## HLE — official judge path (orthogonal)

| Step | Rule |
| --- | --- |
| Dataset | gated HF `cais/hle` — Agree + classic `HF_TOKEN` (session only) |
| Predict | official CAIS `run_model_predictions.py` over **2500** test items |
| Judge | CAIS judge → Accuracy / Calibration in receipt |
| Live | `reports/hle_official_20260721T143509Z/` — leave running; `acc=null` until judge finishes |

**Leave HLE running.** Do not stop for ARC notebook work. Not a Kaggle submit gate.

## Remaining gaps to true competition 100%

| Gap | Status |
| --- | --- |
| AGI-2 platform licensed fill | ❌ **62/259 (23.94%)** (shape 240/259 schema-PASS; identity 197). Wave3 identity-only hybrid in flight. No submit. |
| AGI-2 private-test mastery | ❌ local 172/172 is labeled **eval** only (0 overlap with test IDs) |
| AGI-2 notebook solver quality on private test | ❌ schema ≠ LB 100% |
| AGI-3 private / scored games beyond public triad | ❌ sealed parquet is public-suite WIN; scored rerun may differ |
| AGI-3 full agent binary in air-gapped package | ⚠️ schema path GREEN; full gateway agent wiring optional follow-up |
| Daily quota | ❌ exhausted until ≈ 2026-07-21T23:57Z — **NO submit before reset** |
| HLE judge complete | ❌ preds in flight |

## Git tip

See `git rev-parse HEAD` after GaiaKey push. Prior readiness pack tip around `e848393` / `682eaa1`.

## Notebooks-only path (post-400)

Direct competitions submit refused: daily allowance + **Notebooks only**.

| Track | Path |
| --- | --- |
| AGI-2 | `kaggle/airgap-notebooks/arc-agi-2/affine-agi2-airgap-submit.ipynb` |
| AGI-3 | `kaggle/airgap-notebooks/arc-agi-3/affine-agi3-airgap-submit.ipynb` |

Steward checklist + quota ETA: [`docs/KAGGLE_ARC_NOTEBOOK_SUBMIT.md`](KAGGLE_ARC_NOTEBOOK_SUBMIT.md).
Reminder: `bin/remind-kaggle-notebook-submit.sh`.
**Quota reset ETA:** ≈ **2026-07-21T23:57:04Z UTC**. Lock kept. No Keychain. HLE predict left running.
