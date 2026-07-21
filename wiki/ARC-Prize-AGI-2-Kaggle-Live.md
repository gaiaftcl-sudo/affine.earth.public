# ARC Prize 2026 (ARC-AGI-2) — Kaggle live record

Official competition: [ARC Prize 2026 — ARC-AGI-2](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-2)

## Recorded 2026-07-21

| Check | Observed result |
|:---|:---|
| Competition entry | **Entered** — Kaggle reports `userHasEntered=True` |
| Official data | **Downloaded** — 240 test tasks, 120 evaluation tasks, and 1,000 training tasks |
| Package | `kaggle/arc-prize-2026-agi-2/` on `main`; public-repo code only |
| Submission contract | `submission.json` with `attempt_1` + `attempt_2` for every official test grid |
| Notebook | [Affine ARC Prize 2026 — ARC-AGI-2](https://www.kaggle.com/code/bliztafree/affine-arc-prize-2026-agi-2), **complete**, internet disabled |
| Competition submission | v1 was **accepted** at 2026-07-21 10:32:48 UTC; fresh direct-file and notebook v2 submissions both return HTTP 400 |
| **Public score** | **0.00** — `SubmissionStatus.COMPLETE` |

The package is separate from the ARC-AGI-3 notebook and contains no credentials
or private affine.earth OS source.

## How submission was accepted

ARC-AGI-2 is a **code competition**. Direct file upload returns HTTP 400. The working path is:

```bash
export KAGGLE_API_TOKEN=...   # env only — never Keychain
kaggle kernels push -p kaggle/arc-prize-2026-agi-2
kaggle competitions submit -c arc-prize-2026-arc-agi-2 \
  -k bliztafree/affine-arc-prize-2026-arc-agi-2 \
  -f submission.json -v 1 \
  -m 'ARC-AGI-2 air-gapped public transformation baseline v1'
```

## Evidence

- Local schema validation: 240 official test tasks.
- Offline evaluation set: 0/172 exact grids for this initial transformation baseline.
- Notebook log: `evidence/arc-prize-2026-agi-2/kernel-output/affine-arc-prize-2026-arc-agi-2.log` — wrote `submission.json` for 240 tasks.
- Score receipt: `evidence/arc-prize-2026-agi-2/kaggle-submissions.csv` — publicScore `0.00`.
- Reset evidence: `evidence/arc-prize-2026-agi-2/redo-20260721.md` — fresh
  official-data validation, output match, and the current upload responses.

No signup-video embed is used on this page.
