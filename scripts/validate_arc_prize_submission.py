#!/usr/bin/env python3
"""Validate ARC-AGI-2 submission.json against the official / top-score contract.

Contract sources (local mastery, no submit):
  - official sample_submission.json (240 tasks; attempt_1 + attempt_2)
  - NVARC 2025 baseline notebook get_submission / validate_submission
  - MCP AGI-2 starter notebooks writing /kaggle/working/submission.json

Rules enforced loudly:
  - filename exactly submission.json
  - root object keyed by non-empty task_id strings
  - each task maps to a non-empty list (one entry per test input)
  - each entry has exactly keys attempt_1 and attempt_2
  - each attempt is a non-empty rectangular grid of ints in [0, 9]
  - optional --challenges path: task IDs and list lengths must match
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


MAX_ARC_DIM = 30


def _is_grid(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    width = None
    for row in value:
        if not isinstance(row, list) or not row:
            return False
        if width is None:
            width = len(row)
        elif len(row) != width:
            return False
        if len(row) > MAX_ARC_DIM:
            return False
        for cell in row:
            if type(cell) is not int or cell < 0 or cell > 9:
                return False
    return len(value) <= MAX_ARC_DIM


def validate_submission(path: Path, challenges: Optional[Dict[str, Any]] = None) -> int:
    if path.name != "submission.json":
        raise ValueError(
            f"Submission filename must be exactly submission.json, received {path.name}."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not payload:
        raise ValueError("Submission must be a non-empty task-id object.")

    if challenges is not None:
        expected_ids = set(challenges)
        got_ids = set(payload)
        missing = sorted(expected_ids - got_ids)
        extra = sorted(got_ids - expected_ids)
        if missing or extra:
            raise ValueError(
                f"Task-id drift vs challenges: missing={missing[:8]} extra={extra[:8]} "
                f"(missing_n={len(missing)} extra_n={len(extra)})."
            )

    test_count = 0
    for task_id, predictions in payload.items():
        if not isinstance(task_id, str) or not task_id:
            raise ValueError(f"Task id must be a non-empty string, received {task_id!r}.")
        if not isinstance(predictions, list) or not predictions:
            raise ValueError(f"{task_id!r} must map to a non-empty test-prediction list.")
        if challenges is not None:
            expected_n = len(challenges[task_id]["test"])
            if len(predictions) != expected_n:
                raise ValueError(
                    f"{task_id} prediction count {len(predictions)} != "
                    f"challenge test count {expected_n}."
                )
        for test_index, prediction in enumerate(predictions):
            if not isinstance(prediction, dict):
                raise ValueError(f"{task_id}[{test_index}] must be an object.")
            keys = set(prediction)
            if keys != {"attempt_1", "attempt_2"}:
                raise ValueError(
                    f"{task_id}[{test_index}] must contain exactly attempt_1 and attempt_2, "
                    f"received {sorted(keys)}."
                )
            for attempt in ("attempt_1", "attempt_2"):
                grid = prediction[attempt]
                if not _is_grid(grid):
                    raise ValueError(
                        f"{task_id}[{test_index}].{attempt} is not a valid ARC color grid "
                        f"(non-empty rectangle, ints 0..9, dims ≤ {MAX_ARC_DIM})."
                    )
            test_count += 1

    print(
        f"Validated {path}: {len(payload)} tasks, {test_count} test inputs, "
        "two attempts each (top-score / sample_submission contract)."
    )
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", type=Path)
    parser.add_argument(
        "--challenges",
        type=Path,
        default=None,
        help="Optional official *challenges*.json to enforce task IDs and test counts.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    challenges = None
    if args.challenges is not None:
        challenges = json.loads(args.challenges.read_text(encoding="utf-8"))
        if not isinstance(challenges, dict):
            raise ValueError("Challenges file must be a task-id object.")
    try:
        return validate_submission(args.submission, challenges)
    except Exception as exc:  # noqa: BLE001 — fail loud for local mastery
        print(f"ARC-AGI-2 JSON validation FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
