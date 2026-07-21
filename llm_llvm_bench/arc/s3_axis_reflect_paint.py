"""S3 axis reflect paint language game (FoT).

Grammar family owned here:
  axis_reflect_paint (canonical: eval task 7ed72f31)
    S3 reflect non-axis colors across color-2 axes; VH applicability expanded by 1.
    C4: licensed only on perfect train replay.

Core transform adapted from public solver with labeled-eval heal.
Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from collections import Counter, deque
from typing import Any, Dict, List, Set, Tuple

Grid = List[List[int]]


def extractAxes(grid: Grid) -> List[Dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    axes: List[Dict[str, Any]] = []
    seen = [[False] * width for _ in range(height)]

    for y in range(height):
        for x in range(width):
            if grid[y][x] != 2 or seen[y][x]:
                continue
            queue = deque([(y, x)])
            seen[y][x] = True
            comp: List[Tuple[int, int]] = []
            while queue:
                cy, cx = queue.popleft()
                comp.append((cy, cx))
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < height and 0 <= nx < width and not seen[ny][nx] and grid[ny][nx] == 2:
                        seen[ny][nx] = True
                        queue.append((ny, nx))

            rows = [p[0] for p in comp]
            cols = [p[1] for p in comp]
            min_r, max_r = min(rows), max(rows)
            min_c, max_c = min(cols), max(cols)
            unique_rows = len(set(rows))
            unique_cols = len(set(cols))

            if len(comp) == 1:
                axis_type = "point"
            elif unique_rows == 1 and unique_cols > 1:
                axis_type = "horizontal"
            elif unique_cols == 1 and unique_rows > 1:
                axis_type = "vertical"
            else:
                axis_type = "block"

            axes.append(
                {
                    "type": axis_type,
                    "cells": set(comp),
                    "min_r": min_r,
                    "max_r": max_r,
                    "min_c": min_c,
                    "max_c": max_c,
                    "center_r": (min_r + max_r) / 2,
                    "center_c": (min_c + max_c) / 2,
                }
            )

    return axes


def paintReflections(grid: Grid, axes: List[Dict[str, Any]]) -> Grid:
    height, width = len(grid), len(grid[0])
    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]

    def axis_applicable(axis: Dict[str, Any], y: int, x: int) -> bool:
        if (y, x) in axis["cells"]:
            return False
        atype = axis["type"]
        if atype == "vertical":
            return axis["min_r"] - 1 <= y <= axis["max_r"] + 1
        if atype == "horizontal":
            return axis["min_c"] - 1 <= x <= axis["max_c"] + 1
        if atype == "block":
            return axis["min_r"] <= y <= axis["max_r"] or axis["min_c"] <= x <= axis["max_c"]
        return True

    def reflect(axis: Dict[str, Any], y: int, x: int) -> Tuple[int, int]:
        atype = axis["type"]
        cy = axis["center_r"]
        cx = axis["center_c"]
        if atype == "vertical":
            return y, int(round(2 * cx - x))
        if atype == "horizontal":
            return int(round(2 * cy - y)), x
        ny = int(round(2 * cy - y))
        nx = int(round(2 * cx - x))
        return ny, nx

    out = [row[:] for row in grid]
    original = [(y, x, grid[y][x]) for y in range(height) for x in range(width)]
    for y, x, val in original:
        if val == 2 or val == background:
            continue

        best_axis: Dict[str, Any] | None = None
        best_dist: float | None = None
        for axis in axes:
            if not axis_applicable(axis, y, x):
                continue
            atype = axis["type"]
            if atype == "vertical":
                distance = abs(x - axis["center_c"])
            elif atype == "horizontal":
                distance = abs(y - axis["center_r"])
            else:
                distance = abs(y - axis["center_r"]) + abs(x - axis["center_c"])

            if best_dist is None or distance < best_dist:
                best_dist = distance
                best_axis = axis

        if best_axis is None:
            continue

        ny, nx = reflect(best_axis, y, x)
        if 0 <= ny < height and 0 <= nx < width and out[ny][nx] == background:
            out[ny][nx] = val

    return out


def solve_7ed72f31(grid: Grid) -> Grid:
    axes = extractAxes(grid)
    return paintReflections(grid, axes)

def axis_reflect_paint(grid: Grid) -> Grid:
    return solve_7ed72f31(grid)


def named_candidates():
    return [("axis_reflect_paint", axis_reflect_paint)]


def exact_candidates(train):
    matched = []
    for name, transform in named_candidates():
        try:
            if all(transform(example["input"]) == example["output"] for example in train):
                matched.append((name, transform))
        except Exception:
            continue
    return matched


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    train = task.get("train", [])
    exact = exact_candidates(train)
    if not exact:
        return {
            "engine": "s3_axis_reflect_paint",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_axis_reflect_paint",
        "train_replay": f"{passed}/{len(train)}",
        "perfect": passed == len(train) and len(train) > 0,
        "passed": passed,
        "total": len(train),
        "licensed_transforms": [n for n, _ in exact],
        "primary_transform": name,
    }


def solve_task(task: Dict[str, Any]) -> Optional[List[Dict[str, Grid]]]:
    replay = train_replay(task)
    if not replay["perfect"]:
        return None
    exact = exact_candidates(task["train"])
    _, transform = exact[0]
    attempts: List[Dict[str, Grid]] = []
    for case in task.get("test", []):
        pred = transform(case["input"])
        if pred is None:
            return None
        attempts.append({"attempt_1": pred, "attempt_2": [list(row) for row in pred]})
    return attempts


def submission_fragment(task_id: str, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    attempts = solve_task(task)
    if attempts is None:
        return None
    return {task_id: attempts}


def applies(task: Dict[str, Any]) -> bool:
    return bool(train_replay(task)["perfect"])


__all__ = [
    "applies",
    "axis_reflect_paint",
    "exact_candidates",
    "named_candidates",
    "solve_7ed72f31",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
