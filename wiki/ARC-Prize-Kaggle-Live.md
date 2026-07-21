# ARC Prize 2026 (ARC-AGI-3) — Kaggle live record

Official competition: [ARC Prize 2026 - ARC-AGI-3](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3)

**Format note:** ARC-AGI-3 is an interactive **agent** track. The air-gapped Kaggle output is `submission.parquet`, not classic ARC-AGI-2 `submission.json` with `attempt_1` / `attempt_2` grids. That grid contract belongs to [ARC-AGI-2](ARC-Prize-AGI-2-Kaggle-Live) (sibling track).

Auth for this record: `export KAGGLE_API_TOKEN=…` only. No Keychain / `security` / browser credential APIs.

## Recorded 2026-07-21 (post-join)

| Check | Observed result |
|:---|:---|
| Kaggle account | `bliztafree` |
| `userHasEntered` | **True** |
| Data download | **OK** — `arc-prize-2026-arc-agi-3.zip` (42 MB) under `data/arc-prize-2026/` (gitignored) |
| Competition input shape | Agent framework + `environment_files/` + wheels — **no** `*challenges*.json` |
| Local smoke | Official starter `make verify-local` → aggregate scorecard **0.0** (random baseline) |
| Kernel Phase A | **COMPLETE** — [bliztafree/arc-prize-2026-arc-agi-3-starter](https://www.kaggle.com/code/bliztafree/arc-prize-2026-arc-agi-3-starter) |
| Kernel constraints | `enable_internet=false`, GPU T4, competition source `arc-prize-2026-arc-agi-3` |
| Kernel output | `submission.parquet` (890 B on platform; local copy in evidence) |
| Competition submit | ref **54875048** — `SubmissionStatus.PENDING` (publicScore empty at last poll) |
| Leaderboard score | **Not returned yet** — do not invent a number |

Secret-free evidence under `evidence/arc-prize-2026/`:

- `download.log` — competition zip download
- `verify-local.log` — local agent smoke
- `kaggle-submit.log` — kernel push (Phase A)
- `kaggle-status-final.log` — `KernelWorkerStatus.COMPLETE`
- `kernel-output/submission.parquet` + kernel log
- `kaggle-competition-submit.log` / `kaggle-submissions.log` — Phase B ref `54875048`

**Never commit `KAGGLE_API_TOKEN`.**

## Reproduce (public test repo only)

```bash
export KAGGLE_API_TOKEN=…   # env only; never Keychain
# Official ARC Prize starter (Python 3.12): https://github.com/arcprize/ARC-AGI-3-Kaggle-Starter
# notebooks/kernel-metadata.json id → bliztafree/arc-prize-2026-arc-agi-3-starter
# enable_internet: false
make setup && make verify-local && make submit && make status
# When COMPLETE:
kaggle competitions submit arc-prize-2026-arc-agi-3 \
  -k bliztafree/arc-prize-2026-arc-agi-3-starter \
  -f submission.parquet -v 1 \
  -m "public-test AGI-3 starter baseline"
kaggle competitions submissions -c arc-prize-2026-arc-agi-3
```

When `publicScore` fills in, update this page with the exact platform value and the commit SHA that recorded it.
