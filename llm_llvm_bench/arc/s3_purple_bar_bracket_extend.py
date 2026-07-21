"""S3 purple bar-bracket extend language game (FoT).

Grammar family owned here:
  purple_bar_bracket_extend (canonical: eval task 36a08778)
    S1: same canvas; purple markers = color 6; red bars = color 2.
    S2: purple columns extend downward from the lowest marker row.
    S3: when an extending column hits a red bar on the next row,
        draw a bracket top above the bar and split into side columns.
    S4: never overwrite red bar cells; continue until bottom.
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 36a08778). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_PURPLE = 6
_RED = 2


def purple_bar_bracket_extend(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    if len(out) != len(grid) or len(out[0]) != len(grid[0]):
        return None
    return out


def _solve(grid: Grid) -> Grid:
    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]

    purple_cols: set[int] = set()
    start_row = 0
    for r in range(height):
        for c in range(width):
            if grid[r][c] == _PURPLE:
                purple_cols.add(c)
                start_row = max(start_row, r)

    if not purple_cols:
        return output

    bars_by_row: Dict[int, List[Tuple[int, int]]] = {}
    for r in range(height):
        c = 0
        while c < width:
            if grid[r][c] == _RED:
                start = c
                while c < width and grid[r][c] == _RED:
                    c += 1
                bars_by_row.setdefault(r, []).append((start, c - 1))
            else:
                c += 1

    extending = set(purple_cols)
    for r in range(start_row, height):
        for c in list(extending):
            if output[r][c] != _RED:
                output[r][c] = _PURPLE

        if r + 1 < height and (r + 1) in bars_by_row:
            for s, e in bars_by_row[r + 1]:
                entering = {c for c in extending if s <= c <= e}
                if not entering:
                    continue
                bl = max(0, s - 1)
                br = min(width - 1, e + 1)
                for c in range(bl, br + 1):
                    if output[r][c] != _RED:
                        output[r][c] = _PURPLE
                extending -= entering
                if s - 1 >= 0:
                    extending.add(s - 1)
                if e + 1 < width:
                    extending.add(e + 1)

    return output


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("purple_bar_bracket_extend", purple_bar_bracket_extend)]


def exact_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    matched: List[Tuple[str, Transform]] = []
    for name, transform in named_candidates(train):
        if all(transform(example["input"]) == example["output"] for example in train):
            matched.append((name, transform))
    return matched


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    train = task.get("train", [])
    exact = exact_candidates(train)
    if not exact:
        return {
            "engine": "s3_purple_bar_bracket_extend",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_purple_bar_bracket_extend",
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
    "purple_bar_bracket_extend",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
