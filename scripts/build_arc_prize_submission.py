#!/usr/bin/env python3
"""Build the ARC Prize `submission.json` contract from official challenge data.

The producer is intentionally offline after the official competition input has
been mounted. A local Affine solver may be supplied as a command that accepts
one JSON request on stdin and writes one grid JSON value on stdout.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

Grid = List[List[int]]


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


def _read_challenges(input_dir: Path) -> Dict[str, Dict[str, Any]]:
    candidates = sorted(input_dir.rglob("*test*challenges*.json"))
    if not candidates:
        candidates = sorted(input_dir.rglob("*challenges*.json"))
    if not candidates:
        raise FileNotFoundError(
            f"No official ARC challenge JSON found under {input_dir}. "
            "Mount the Kaggle competition input before running this producer."
        )

    for candidate in candidates:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and all(
            isinstance(task, dict) and isinstance(task.get("test"), list)
            for task in payload.values()
        ):
            return payload
    raise ValueError("Challenge JSON does not contain task_id -> {test: [...]} records.")


def _identity_prediction(grid: Grid) -> Grid:
    """Deterministic baseline when no local solver has been wired."""
    return [list(row) for row in grid]


def _solver_from_command(command: str) -> Callable[[str, int, Dict[str, Any]], Grid]:
    def solve(task_id: str, test_index: int, task: Dict[str, Any]) -> Grid:
        request = {
            "task_id": task_id,
            "test_index": test_index,
            "train": task.get("train", []),
            "test_input": task["test"][test_index]["input"],
        }
        process = subprocess.run(
            command,
            shell=True,
            input=json.dumps(request),
            text=True,
            capture_output=True,
            check=False,
        )
        if process.returncode != 0:
            raise RuntimeError(
                f"Local ARC solver failed for {task_id}[{test_index}]: "
                f"{process.stderr.strip() or process.stdout.strip()}"
            )
        prediction = json.loads(process.stdout)
        if not _is_grid(prediction):
            raise ValueError(f"Local ARC solver returned an invalid grid for {task_id}[{test_index}].")
        return prediction

    return solve


def build_submission(
    challenges: Dict[str, Dict[str, Any]],
    solver: Optional[Callable[[str, int, Dict[str, Any]], Grid]] = None,
) -> Dict[str, List[Dict[str, Grid]]]:
    """Return exactly two predictions for every official test input."""
    submission: Dict[str, List[Dict[str, Grid]]] = {}
    for task_id, task in challenges.items():
        entries: List[Dict[str, Grid]] = []
        for test_index, test_case in enumerate(task["test"]):
            grid = test_case.get("input")
            if not _is_grid(grid):
                raise ValueError(f"Official input grid is invalid for {task_id}[{test_index}].")
            first = solver(task_id, test_index, task) if solver else _identity_prediction(grid)
            if not _is_grid(first):
                raise ValueError(f"Attempt 1 is invalid for {task_id}[{test_index}].")
            # ARC Prize scoring accepts either attempt; the second mandatory
            # attempt is independent at the schema boundary and deterministic
            # until a second local Affine strategy is wired.
            second = _identity_prediction(grid)
            entries.append({"attempt_1": first, "attempt_2": second})
        submission[task_id] = entries
    return submission


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Produce ARC Prize submission.json offline.")
    parser.add_argument("--input-dir", required=True, type=Path, help="Mounted Kaggle input root.")
    parser.add_argument(
        "--output-dir",
        default=Path("."),
        type=Path,
        help="Directory that will receive the required submission.json filename.",
    )
    parser.add_argument(
        "--solver-command",
        default=os.environ.get("AFFINE_ARC_SOLVER_COMMAND", ""),
        help="Optional local solver command; receives one request JSON via stdin.",
    )
    args = parser.parse_args(argv)

    challenges = _read_challenges(args.input_dir)
    solver = _solver_from_command(args.solver_command) if args.solver_command else None
    submission = build_submission(challenges, solver)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "submission.json"
    output.write_text(json.dumps(submission, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {output} with {sum(len(items) for items in submission.values())} test inputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
