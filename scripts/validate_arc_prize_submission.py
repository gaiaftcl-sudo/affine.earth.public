#!/usr/bin/env python3
"""Validate the two-attempt ARC Prize JSON submission contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Optional


def _is_grid(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(
            isinstance(row, list)
            and bool(row)
            and all(isinstance(cell, int) and 0 <= cell <= 9 for cell in row)
            for row in value
        )
    )


def validate_submission(path: Path) -> int:
    if path.name != "submission.json":
        raise ValueError(f"Submission filename must be exactly submission.json, received {path.name}.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not payload:
        raise ValueError("Submission must be a non-empty task-id object.")
    test_count = 0
    for task_id, predictions in payload.items():
        if not isinstance(task_id, str) or not isinstance(predictions, list) or not predictions:
            raise ValueError(f"{task_id!r} must map to a non-empty test-prediction list.")
        for test_index, prediction in enumerate(predictions):
            if set(prediction) != {"attempt_1", "attempt_2"}:
                raise ValueError(f"{task_id}[{test_index}] must contain exactly attempt_1 and attempt_2.")
            for attempt in ("attempt_1", "attempt_2"):
                if not _is_grid(prediction[attempt]):
                    raise ValueError(f"{task_id}[{test_index}].{attempt} is not a valid ARC color grid.")
            test_count += 1
    print(f"Validated {path}: {len(payload)} tasks, {test_count} test inputs, two attempts each.")
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", type=Path)
    args = parser.parse_args(argv)
    return validate_submission(args.submission)


if __name__ == "__main__":
    raise SystemExit(main())
