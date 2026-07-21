"""Air-gapped ARC-AGI-2 submission entrypoint for Kaggle."""

import argparse
import json
from collections import Counter
from pathlib import Path


def rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def rotate_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def flip_horizontal(grid):
    return [row[::-1] for row in grid]


def flip_vertical(grid):
    return grid[::-1]


def transpose(grid):
    return [list(row) for row in zip(*grid)]


def anti_transpose(grid):
    return rotate_180(transpose(grid))


def background(grid):
    return Counter(cell for row in grid for cell in row).most_common(1)[0][0]


def crop_foreground(grid):
    bg = background(grid)
    positions = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, cell in enumerate(row)
        if cell != bg
    ]
    if not positions:
        return [list(row) for row in grid]
    rows, columns = zip(*positions)
    return [
        row[min(columns) : max(columns) + 1]
        for row in grid[min(rows) : max(rows) + 1]
    ]


def recolor_by_training_pairs(train):
    mapping = {}
    for example in train:
        source, target = example["input"], example["output"]
        if len(source) != len(target) or any(
            len(left) != len(right) for left, right in zip(source, target)
        ):
            return None
        for source_row, target_row in zip(source, target):
            for source_cell, target_cell in zip(source_row, target_row):
                if source_cell in mapping and mapping[source_cell] != target_cell:
                    return None
                mapping[source_cell] = target_cell
    return mapping


def recolor(grid, mapping):
    return [[mapping.get(cell, cell) for cell in row] for row in grid]


def named_candidates(train):
    transforms = [
        ("identity", lambda grid: [list(row) for row in grid]),
        ("rotate_cw", rotate_cw),
        ("rotate_180", rotate_180),
        ("rotate_ccw", rotate_ccw),
        ("flip_horizontal", flip_horizontal),
        ("flip_vertical", flip_vertical),
        ("transpose", transpose),
        ("anti_transpose", anti_transpose),
        ("crop_foreground", crop_foreground),
    ]
    candidates = list(transforms)
    color_mapping = recolor_by_training_pairs(train)
    if color_mapping is not None:
        candidates.append(("recolor", lambda grid: recolor(grid, color_mapping)))
    return candidates


def exact_candidates(train):
    matched = []
    for name, transform in named_candidates(train):
        if all(transform(example["input"]) == example["output"] for example in train):
            matched.append((name, transform))
    return matched


def predictions(task, test_input):
    candidates = exact_candidates(task["train"])
    if not candidates:
        candidates = named_candidates(task["train"])
    first_name, first = candidates[0]
    first_grid = first(test_input)
    alternate = next(
        (
            transform
            for name, transform in candidates
            if name != first_name and transform(test_input) != first_grid
        ),
        lambda grid: [list(row) for row in grid],
    )
    return {"attempt_1": first_grid, "attempt_2": alternate(test_input)}


def find_challenges(input_root):
    candidates = sorted(input_root.rglob("arc-agi_test_challenges.json"))
    if len(candidates) != 1:
        raise RuntimeError("Expected exactly one official ARC-AGI-2 test challenge file.")
    return json.loads(candidates[0].read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", default="/kaggle/input")
    parser.add_argument("--output", default="submission.json")
    arguments = parser.parse_args()

    submission = {}
    for task_id, task in find_challenges(Path(arguments.input_root)).items():
        submission[task_id] = [predictions(task, test["input"]) for test in task["test"]]
    Path(arguments.output).write_text(
        json.dumps(submission, separators=(",", ":")), encoding="utf-8"
    )
    print(f"Wrote {arguments.output} for {len(submission)} ARC-AGI-2 tasks.")


if __name__ == "__main__":
    main()
