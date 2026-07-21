"""Air-gapped Kaggle kernel entrypoint for ARC Prize 2026."""

import json
import os
import subprocess
from pathlib import Path


def is_grid(value):
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


def challenges_from_input(input_root):
    candidates = sorted(input_root.rglob("*test*challenges*.json"))
    if not candidates:
        candidates = sorted(input_root.rglob("*challenges*.json"))
    for candidate in candidates:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and all(
            isinstance(task, dict) and isinstance(task.get("test"), list)
            for task in payload.values()
        ):
            return payload
    raise RuntimeError("Official ARC challenge JSON was not mounted in the Kaggle input.")


def solve_with_affine(command, task_id, test_index, task):
    request = {
        "task_id": task_id,
        "test_index": test_index,
        "train": task.get("train", []),
        "test_input": task["test"][test_index]["input"],
    }
    completed = subprocess.run(
        command,
        shell=True,
        input=json.dumps(request),
        text=True,
        capture_output=True,
        check=True,
    )
    prediction = json.loads(completed.stdout)
    if not is_grid(prediction):
        raise RuntimeError("Affine ARC adapter returned an invalid color grid.")
    return prediction


def main():
    input_root = Path("/kaggle/input")
    command = os.environ.get("AFFINE_ARC_SOLVER_COMMAND", "")
    submission = {}
    for task_id, task in challenges_from_input(input_root).items():
        predictions = []
        for test_index, test_case in enumerate(task["test"]):
            source_grid = test_case["input"]
            if not is_grid(source_grid):
                raise RuntimeError("Official ARC input contains an invalid color grid.")
            first = solve_with_affine(command, task_id, test_index, task) if command else source_grid
            # Both mandatory attempts are written for every test input. Until a
            # second local Affine strategy is configured, attempt_2 preserves
            # the original grid as a deterministic alternative.
            predictions.append(
                {"attempt_1": first, "attempt_2": [list(row) for row in source_grid]}
            )
        submission[task_id] = predictions
    Path("submission.json").write_text(
        json.dumps(submission, separators=(",", ":")), encoding="utf-8"
    )
    print("Wrote submission.json with two attempts per official test input.")


if __name__ == "__main__":
    main()
