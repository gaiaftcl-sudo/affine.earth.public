#!/usr/bin/env python3
"""Validate ARC-AGI-3 submission.parquet against the top-score / starter schema.

Contract reverse-engineered from public notebooks (inversion Stochastic Goose,
pscamillo starter, jeroencottaar simplified) and our scored probe
(ref 54875048, publicScore 0.12):

  columns (exact order): row_id, game_id, end_of_game, score
  dtypes: string/object, string/object, bool, integer
  filename: submission.parquet
  write with index=False

Format acceptance ≠ puzzle mastery. A schema-valid parquet can score low
(our 0.12) while top leaderboard scores (~1.5–1.86) reflect agent policy.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Optional

EXPECTED_COLUMNS = ["row_id", "game_id", "end_of_game", "score"]


def validate_submission(path: Path) -> int:
    if path.name != "submission.parquet":
        raise ValueError(
            f"Submission filename must be exactly submission.parquet, received {path.name}."
        )
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("pandas is required to validate ARC-AGI-3 parquet") from exc

    frame = pd.read_parquet(path)
    columns = list(frame.columns)
    if columns != EXPECTED_COLUMNS:
        raise ValueError(
            f"Parquet columns must be exactly {EXPECTED_COLUMNS}, received {columns}."
        )
    if frame.empty:
        raise ValueError("submission.parquet must contain at least one row.")

    for column in ("row_id", "game_id"):
        series = frame[column]
        if not (
            pd.api.types.is_string_dtype(series)
            or pd.api.types.is_object_dtype(series)
        ):
            raise ValueError(f"{column} must be string/object dtype, received {series.dtype}.")
        if series.isna().any() or (series.astype(str) == "").any():
            raise ValueError(f"{column} must be non-empty for every row.")

    end = frame["end_of_game"]
    if not pd.api.types.is_bool_dtype(end):
        # Accept nullable boolean only if every value is True/False.
        coerced = end.map(lambda value: value if isinstance(value, bool) else None)
        if coerced.isna().any():
            raise ValueError(
                f"end_of_game must be bool dtype, received {end.dtype}."
            )
    score = frame["score"]
    if not pd.api.types.is_integer_dtype(score):
        raise ValueError(f"score must be integer dtype, received {score.dtype}.")
    if score.isna().any():
        raise ValueError("score must be non-null for every row.")

    print(
        f"Validated {path}: {len(frame)} rows, columns={columns}, "
        f"dtypes={[str(frame[c].dtype) for c in columns]}."
    )
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        return validate_submission(args.submission)
    except Exception as exc:  # noqa: BLE001 — fail loud for local mastery
        print(f"ARC-AGI-3 parquet validation FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
