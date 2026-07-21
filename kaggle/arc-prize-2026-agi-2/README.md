# ARC Prize 2026 — ARC-AGI-2

Standalone Kaggle package for `arc-prize-2026-arc-agi-2`.

`arc_agi_2_kaggle.py` is an air-gapped inference entrypoint. It reads only the
official competition JSON mounted under `/kaggle/input`, derives candidate
grid transformations from each task's training pairs, and writes the required
`submission.json` with two grid attempts for every official test input.

The package contains no credentials and does not import code from the private
affine.earth OS.
