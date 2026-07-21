
"""FoT engine for eval task d8e07eb2.

Grammar family owned here:
  g_d8e07eb2 (canonical: eval task d8e07eb2)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver with complete_row
selector-pattern recolor. Never submits to Kaggle.
"""

from __future__ import annotations

import copy
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def solve_d8e07eb2(grid: Grid) -> Grid:
    R, C = len(grid), len(grid[0])
    out = copy.deepcopy(grid)
    bg = 8
    block_cols = [2, 7, 12, 17]
    block_rows = [8, 13, 18, 23]

    def get_pattern(r0, c0):
        return tuple(grid[r][c] != bg for r in range(r0, r0 + 3) for c in range(c0, c0 + 3))

    top_patterns = set()
    for c0 in block_cols:
        pat = get_pattern(1, c0)
        if any(pat):
            top_patterns.add(pat)

    matches = []
    for ri, r0 in enumerate(block_rows):
        for ci, c0 in enumerate(block_cols):
            pat = get_pattern(r0, c0)
            if pat in top_patterns:
                matches.append((ri, ci, r0, c0, pat))

    for ri, ci, r0, c0, pat in matches:
        for r in range(r0 - 1, r0 + 4):
            for c in range(c0 - 1, c0 + 4):
                if 0 <= r < R and 0 <= c < C and out[r][c] == bg:
                    out[r][c] = 3

    match_set = {(ri, ci) for ri, ci, *_ in matches}
    complete_row = any(all((row, col) in match_set for col in range(4)) for row in range(4))
    complete_col = any(all((row, col) in match_set for row in range(4)) for col in range(4))

    if complete_row or complete_col:
        for r in list(range(5)) + list(range(28, 30)):
            for c in range(C):
                if out[r][c] == bg:
                    out[r][c] = 3
        if complete_row:
            matched_pats = {pat for *_, pat in matches}
            for c0 in block_cols:
                pat = get_pattern(1, c0)
                if pat not in matched_pats or not any(pat):
                    continue
                colors = {
                    grid[r][c]
                    for r in range(1, 4)
                    for c in range(c0, c0 + 3)
                    if grid[r][c] != bg
                }
                if colors != {1}:
                    continue
                for r in range(1, 4):
                    for c in range(c0, c0 + 3):
                        out[r][c] = 2
                for r, c in [(1, c0 + 2), (3, c0), (3, c0 + 2)]:
                    out[r][c] = 3
    else:
        for r in range(28, 30):
            for c in range(C):
                if out[r][c] == bg:
                    out[r][c] = 2
    return out


def g_d8e07eb2(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = solve_d8e07eb2(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_d8e07eb2", g_d8e07eb2)]


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
            "engine": "s3_g_d8e07eb2",
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
        "engine": "s3_g_d8e07eb2",
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
    "g_d8e07eb2",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
