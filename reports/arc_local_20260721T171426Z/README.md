# ARC-AGI-3 independent re-verify — 20260721T171426Z

One harness pass: `--games bp35 ar25 ls20 --max-actions 500`.

| Game | Levels | WIN |
| --- | ---: | --- |
| bp35 | 9/9 | yes |
| ar25 | 8/8 | yes |
| ls20 | 7/7 | yes |

- `win_terminals=3`, `game_over_events=0`, `submission_blocked=true`
- Parquet: `submission.parquet` (validated schema; scores 9/8/7)
- Lock: `configs/NO_KAGGLE_SUBMIT.lock` intact
- Captures: `affine_audit_logs/arc_agi3/{bp35,ar25,ls20}/20260721T171*/`
