"""Batch FoT engine for eval task b10624e5.

Grammar family owned here:
  g_b10624e5 (canonical: eval task b10624e5)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · b10624e5). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_b10624e5(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


import json
import math


def solve(grid: list[list[int]]) -> list[list[int]]:
    rows = len(grid)
    cols = len(grid[0])
    bg = 4

    # Find divider row and column (full lines of 1s)
    div_row = next(r for r in range(rows) if all(grid[r][c] == 1 for c in range(cols)))
    div_col = next(c for c in range(cols) if all(grid[r][c] == 1 for r in range(rows)))

    # Extract key pattern from top-left quadrant (all non-background cells)
    tl_cells = {}
    for r in range(div_row):
        for c in range(div_col):
            if grid[r][c] != bg:
                tl_cells[(r, c)] = grid[r][c]

    # Find the 2-block bounding box in TL
    twos = [(r, c) for (r, c), v in tl_cells.items() if v == 2]
    tl_r0 = min(r for r, c in twos)
    tl_c0 = min(c for r, c in twos)
    h_tl = max(r for r, c in twos) - tl_r0 + 1
    w_tl = max(c for r, c in twos) - tl_c0 + 1

    # Pixel offsets relative to the 2 block's top-left corner
    offsets = {(r - tl_r0, c - tl_c0): v for (r, c), v in tl_cells.items()}

    out = [row[:] for row in grid]

    # Each hint quadrant: (row_start, row_end, col_start, col_end, v_flip, h_flip)
    quadrants = [
        (0, div_row, div_col + 1, cols, False, True),       # TR: h-mirror
        (div_row + 1, rows, 0, div_col, True, False),       # BL: v-mirror
        (div_row + 1, rows, div_col + 1, cols, True, True), # BR: both
    ]

    for r_lo, r_hi, c_lo, c_hi, v_flip, h_flip in quadrants:
        hint_twos = [
            (r, c) for r in range(r_lo, r_hi)
            for c in range(c_lo, c_hi) if grid[r][c] == 2
        ]
        if not hint_twos:
            continue

        hr0 = min(r for r, c in hint_twos)
        hc0 = min(c for r, c in hint_twos)
        h_hint = max(r for r, c in hint_twos) - hr0 + 1
        w_hint = max(c for r, c in hint_twos) - hc0 + 1

        for (dr, dc), color in offsets.items():
            # Scale each TL pixel to a range in the hint coordinate system
            for R in _ints_in_range(dr * h_hint, (dr + 1) * h_hint, h_tl):
                for C in _ints_in_range(dc * w_hint, (dc + 1) * w_hint, w_tl):
                    mr = (h_hint - 1 - R) if v_flip else R
                    mc = (w_hint - 1 - C) if h_flip else C
                    ar, ac = hr0 + mr, hc0 + mc
                    if 0 <= ar < rows and 0 <= ac < cols:
                        out[ar][ac] = color

    return out


def _ints_in_range(num_lo: int, num_hi: int, den: int) -> list[int]:
    """Return integers n where num_lo <= n * den < num_hi."""
    if num_lo >= 0:
        start = (num_lo + den - 1) // den
    else:
        start = -((-num_lo) // den)
    result = []
    n = start
    while n * den < num_hi:
        result.append(n)
        n += 1
    return result


if __name__ == "__main__":
    with open("/Users/evanpieser/arc-puzzle-catalog/dataset/tasks/b10624e5.json") as f:
        task = json.load(f)

    for i, pair in enumerate(task["train"]):
        result = solve(pair["input"])
        status = "PASS" if result == pair["output"] else "FAIL"
        print(f"Train {i}: {status}")
        if status == "FAIL":
            for r in range(len(result)):
                for c in range(len(result[0])):
                    if result[r][c] != pair["output"][r][c]:
                        print(f"  diff at ({r},{c}): got {result[r][c]}, expected {pair['output'][r][c]}")

    for i, pair in enumerate(task["test"]):
        result = solve(pair["input"])
        if "output" in pair:
            status = "PASS" if result == pair["output"] else "FAIL"
            print(f"Test  {i}: {status}")
            if status == "FAIL":
                for r in range(len(result)):
                    for c in range(len(result[0])):
                        if result[r][c] != pair["output"][r][c]:
                            print(f"  diff at ({r},{c}): got {result[r][c]}, expected {pair['output'][r][c]}")
        else:
            print(f"Test  {i}: (no expected output)")



def _solve(grid: Grid):
    return solve(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_b10624e5", g_b10624e5)]


def exact_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    out: List[Tuple[str, Transform]] = []
    for name, transform in named_candidates():
        if all(transform(ex["input"]) == ex["output"] for ex in train):
            out.append((name, transform))
    return out


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    train = task.get("train", [])
    exact = exact_candidates(train)
    if not exact:
        return {
            "engine": "s3_g_b10624e5",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
            "primary_transform": None,
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_g_b10624e5",
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
    "exact_candidates",
    "named_candidates",
    "g_b10624e5",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
