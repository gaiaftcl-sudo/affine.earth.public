"""S3 staircase interior fill language game (FoT).

Grammar family owned here:
  staircase_interior_fill (canonical: eval task 28a6681f)
    S1: same canvas shape; background = 0; blue = 1.
    S2: strip all blue; N = original blue count (conserved).
    S3: Type A = empty cells whose nearest non-bg left and right
        colors match (closed staircase gaps), stacked from the floor.
    S4: Type B = empty cells with a non-bg left neighbor only
        (open side extensions). Fill all valid Type A, then Type B
        bottom-up until N blues are placed.
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 28a6681f). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_BG = 0
_BLUE = 1


def staircase_interior_fill(grid: Grid) -> Optional[Grid]:
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
    rows, cols = len(grid), len(grid[0])
    clean = [
        [_BG if grid[r][c] == _BLUE else grid[r][c] for c in range(cols)]
        for r in range(rows)
    ]
    n_blue = sum(1 for r in range(rows) for c in range(cols) if grid[r][c] == _BLUE)

    raw_type_a: set[Tuple[int, int]] = set()
    type_b: List[Tuple[int, int]] = []
    for r in range(rows):
        for c in range(cols):
            if clean[r][c] != _BG:
                continue
            l_color = None
            for cc in range(c - 1, -1, -1):
                if clean[r][cc] != _BG:
                    l_color = clean[r][cc]
                    break
            r_color = None
            for cc in range(c + 1, cols):
                if clean[r][cc] != _BG:
                    r_color = clean[r][cc]
                    break
            if l_color is not None and r_color is not None and l_color == r_color:
                raw_type_a.add((r, c))
            elif l_color is not None:
                type_b.append((r, c))

    valid_a: set[Tuple[int, int]] = set()
    for r in range(rows - 1, -1, -1):
        for c in range(cols):
            if (r, c) not in raw_type_a:
                continue
            if r == rows - 1 or clean[r + 1][c] != _BG or (r + 1, c) in valid_a:
                valid_a.add((r, c))

    type_a = sorted(valid_a, key=lambda x: (-x[0], x[1]))
    type_b.sort(key=lambda x: (-x[0], x[1]))

    result = [row[:] for row in clean]
    filled = 0
    for r, c in type_a:
        if filled >= n_blue:
            break
        result[r][c] = _BLUE
        filled += 1
    for r, c in type_b:
        if filled >= n_blue:
            break
        result[r][c] = _BLUE
        filled += 1
    return result


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("staircase_interior_fill", staircase_interior_fill)]


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
            "engine": "s3_staircase_interior_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_staircase_interior_fill",
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
    "solve_task",
    "staircase_interior_fill",
    "submission_fragment",
    "train_replay",
]
