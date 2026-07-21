# ARC Prize 2026 (ARC-AGI-3) — Kaggle live record

Official competition: [ARC Prize 2026 - ARC-AGI-3](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3)

Package on `main`: air-gapped notebook under `kaggle/arc-prize-2026/`, producer/validator under `scripts/`, runner `bin/run-arc-prize-kaggle.sh`.

## Recorded 2026-07-21

| Check | Observed result |
|:---|:---|
| Kaggle CLI | Authenticated as `bliztafree` (`kaggle` 1.7.4.5; token via env / `~/.kaggle/kaggle.json`) |
| Competition list | `userHasEntered=False` for `arc-prize-2026-arc-agi-3` |
| Data list API | HTTP 200 (file listing visible) |
| Data download | **403 Forbidden** on `competitions/data/download-all/arc-prize-2026-arc-agi-3` |
| Kernel push | Rejected: *You must accept this competition's rules before you'll be able to add it as a datasource* |
| Local producer | No mounted challenge JSON → no `submission.json` |
| Leaderboard score | **None** — no submission possible until rules are accepted |
| Browser automation | Cursor IDE browser could not open a logged-in Kaggle session (no usable tab / no cookie handshake from API token) |

This page records a **steward rules gate**, not a score. Competition is kernels-submissions-only (`isKernelsSubmissionsOnly=true`).

Secret-free evidence:

- `evidence/arc-prize-2026/kaggle-notebook-push.log` — kernel push rejection
- `evidence/arc-prize-2026/local-producer.log` — missing official input mount
- `evidence/arc-prize-2026/rules-gate-check.log` — re-check of `userHasEntered` + download 403

**Never commit `KAGGLE_API_TOKEN`.** Use env or an out-of-repo env file from `configs/arc-prize-kaggle.env.example`.

## Steward action required (human click)

Kaggle does **not** allow accepting competition rules via the API token alone. A logged-in browser session must accept the rules once.

1. Open this URL while logged in as the same Kaggle account that owns the API token (`bliztafree`):

   **https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/rules**

2. Click **I Understand and Accept** / **Join Competition** (wording on the page).

3. Confirm entry (should print `True`):

   ```bash
   kaggle competitions list -s arc-prize-2026-arc-agi-3 --csv | head
   ```

4. Re-run the package:

   ```bash
   # Download competition data (local mirror for producer)
   mkdir -p data/arc-prize-2026
   kaggle competitions download -c arc-prize-2026-arc-agi-3 -p data/arc-prize-2026
   unzip -o data/arc-prize-2026/arc-prize-2026-arc-agi-3.zip -d data/arc-prize-2026

   # Build + validate submission.json (attempt_1 + attempt_2)
   ./bin/run-arc-prize-kaggle.sh \
     --input-dir data/arc-prize-2026 \
     --output-dir reports/arc-prize-2026

   # Push air-gapped notebook (internet disabled in kernel-metadata)
   ./bin/run-arc-prize-kaggle.sh --push-notebook
   ```

Until step 2 completes, every download / notebook / score path stays blocked. After accept, update this page with `userHasEntered=true`, submission SHA/path, and the returned Kaggle score — do not invent a score before the platform returns one.
