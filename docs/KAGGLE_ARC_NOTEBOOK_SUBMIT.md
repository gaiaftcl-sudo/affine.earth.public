# Kaggle ARC — notebooks-only submit (air-gap)

Direct `kaggle competitions submit` for both ARC Prize 2026 tracks returns
**HTTP 400**: daily allowance (1) **and** **Notebooks only**.

Standing probe refs (do not burn another junk probe):

| Track | Ref | publicScore |
| --- | --- | --- |
| ARC-AGI-2 | **54875115** | **0.00** |
| ARC-AGI-3 | **54875048** | **0.12** |

`configs/NO_KAGGLE_SUBMIT.lock` stays. Direct CLI only with steward
`ALLOW_KAGGLE_SUBMIT=1` (still useless until Notebooks path is used).

## Notebook paths

| Track | Kernel directory | Notebook |
| --- | --- | --- |
| AGI-2 | `kaggle/airgap-notebooks/arc-agi-2/` | `affine-agi2-airgap-submit.ipynb` |
| AGI-3 | `kaggle/airgap-notebooks/arc-agi-3/` | `affine-agi3-airgap-submit.ipynb` |

Rebuild (offline, no submit):

```bash
python3 scripts/build_arc_airgap_kaggle_notebooks.py --root .
# optional: swap AGI-2 platform JSON after hybrid test regen finishes
python3 scripts/build_arc_airgap_kaggle_notebooks.py --root . \
  --agi2-platform-json reports/airgap_agi2_test_*/submission.json
```

### Embedded payloads

| File | Role | SHA-256 |
| --- | --- | --- |
| `arc-agi-2/payload/fot_eval_mastery_submission.json` | FoT labeled-eval **172/172** (120 tasks) | `3e27792b45d4f186ca436d042841c7db5a7164e71a4a018da1b01a894719e082` |
| `arc-agi-2/payload/submission.json` | Platform **shape** 240 tasks / 259 grids | see `MANIFEST.json` |
| `arc-agi-3/payload/submission.parquet` | FoT suite WIN bp35/ar25/ls20 | `9ffc90cee088b086e5d2539abee76b77346191666a657dd63dbf3cf0de340c73` |

### CRITICAL — AGI-2 licensed fill (not shape)

| Metric | Meaning | Gate |
| --- | --- | --- |
| Shape | 240 tasks · 259 grids · two attempts | schema validator PASS |
| Licensed `N/259` | grids where `attempt_1 ≠ test input` (non-identity) | **must be 259/259** before claiming 100% |
| Current platform | measure via `bin/prepare-kaggle-notebook-submit.sh` | **NOT 100%** until peer hybrid closes |

Do **not** read “240/259” as a score. That string is shape (tasks/grids). Peer
`scripts/build_agi2_test_submission_hybrid.py` is closing licensed fill to
**259/259**. Rebuild airgap notebooks after hybrid lands:

```bash
python3 scripts/build_arc_airgap_kaggle_notebooks.py --root . \
  --agi2-platform-json reports/airgap_agi2_test_*/submission.json
```

Internet disabled in `kernel-metadata.json`. Solving is offline; notebook only
materializes `/kaggle/working/submission.json|parquet`.

Format doctrine: [KAGGLE_ARC_TOP_SCORE_FORMATS.md](KAGGLE_ARC_TOP_SCORE_FORMATS.md).

## Steward checklist (after UTC quota reset)

Quota message at 2026-07-21T17:39:04Z said **~6.3h** → retry window
**≈ 2026-07-21T23:57:04Z UTC** (≈ 19:57 EDT).

### Per track (AGI-2 then AGI-3, or reverse — **1 submit/day each**)

1. Confirm lock still present: `test -f configs/NO_KAGGLE_SUBMIT.lock`
2. Open Kaggle → Code → New Notebook **or** push kernel folder:
   ```bash
   # optional push (does not competition-submit):
   export KAGGLE_API_TOKEN=…   # env only — no Keychain
   kaggle kernels push -p kaggle/airgap-notebooks/arc-agi-2
   kaggle kernels push -p kaggle/airgap-notebooks/arc-agi-3
   ```
3. Attach competition data source (`arc-prize-2026-arc-agi-2` / `-agi-3`).
4. Confirm **Internet OFF**, accelerator none (air-gap).
5. **Run All** — verify Output contains:
   - AGI-2: `submission.json`
   - AGI-3: `submission.parquet`
6. **Save Version** (Save & Run All).
7. From the completed version → **Submit to Competition**.
8. Poll score; compare to standing refs above. Do not re-submit the same day.

### Optional API path (after reset, no junk file upload)

```bash
# Kernels push + kernels status only. Competition submit from notebook UI
# (or kernels output → competitions submit of the *notebook* artifact if API allows).
# NEVER: ALLOW_KAGGLE_SUBMIT=1 bin/kaggle-competitions-submit.sh -f <raw json/parquet>
# until platform accepts non-notebook uploads again.
```

Reminder helper: `bin/remind-kaggle-notebook-submit.sh` (prints ETA; does not submit).

## Auth

`export KAGGLE_API_TOKEN=…` (+ username/key if needed). **No Keychain.**

## HLE

Official predict continues under `reports/hle_official_20260721T143509Z/` — orthogonal.
