# Air-gapped ARC Prize notebooks

Internet off. Embed verified local mastery. Emit platform `submission.json` /
`submission.parquet` under `/kaggle/working`.

| Track | Path |
| --- | --- |
| AGI-2 | `arc-agi-2/affine-agi2-airgap-submit.ipynb` |
| AGI-3 | `arc-agi-3/affine-agi3-airgap-submit.ipynb` |

Steward steps: [`docs/KAGGLE_ARC_NOTEBOOK_SUBMIT.md`](../../docs/KAGGLE_ARC_NOTEBOOK_SUBMIT.md).

Rebuild: `python3 scripts/build_arc_airgap_kaggle_notebooks.py`

**No competition submit from this directory** while `configs/NO_KAGGLE_SUBMIT.lock` is present.
