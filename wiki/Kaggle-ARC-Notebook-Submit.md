# Kaggle ARC — notebooks-only submit (air-gap)

Direct `competitions submit` → **HTTP 400**: daily allowance (1) + **Notebooks only**.

Standing probes: AGI-2 **54875115** / **0.00** · AGI-3 **54875048** / **0.12**.

## Air-gap notebooks

| Track | Path |
| --- | --- |
| AGI-2 | `kaggle/airgap-notebooks/arc-agi-2/affine-agi2-airgap-submit.ipynb` |
| AGI-3 | `kaggle/airgap-notebooks/arc-agi-3/affine-agi3-airgap-submit.ipynb` |

Internet **OFF**. Embeds verified FoT artifacts; writes `/kaggle/working/submission.json|parquet`.

**AGI-2 gate:** platform shape = 240 tasks / 259 grids (schema). Licensed fill =
**N/259** (non-identity grids). **Do not claim 100% until 259/259.** Peer hybrid
in flight; tip airgap pack `8776e73` / `b16c8b1`. Measure:
`bin/prepare-kaggle-notebook-submit.sh --dry-run-only`.

## Quota wait window

From 2026-07-21T17:39:04Z + ~6.3h → retry ≈ **2026-07-21T23:57:04Z UTC**.
**NO submit before reset.**

## Steward steps

1. Keep `configs/NO_KAGGLE_SUBMIT.lock`
2. Upload / `kaggle kernels push` the airgap notebook folder
3. Competition data attached · Internet off
4. **Run All** → confirm Output artifact
5. **Save Version** → **Submit to Competition**
6. Do not burn another raw-file probe

Full checklist: repo `docs/KAGGLE_ARC_NOTEBOOK_SUBMIT.md`.
Reminder (no submit): `bin/remind-kaggle-notebook-submit.sh`.

Live records: [ARC-AGI-2](ARC-Prize-AGI-2-Kaggle-Live) · [ARC-AGI-3](ARC-Prize-Kaggle-Live).
Formats: [Kaggle-ARC-Top-Score-Formats](Kaggle-ARC-Top-Score-Formats).
