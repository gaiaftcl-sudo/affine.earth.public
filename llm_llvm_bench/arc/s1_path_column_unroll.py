"""S1 path-column unroll language game (FoT).

Grammar family owned here:
  path_column_unroll (canonical: eval task 7b5033c1)
    S1: majority color is background; non-bg cells form a simple 4-path.
    S2: exactly two degree-1 endpoints; no junctions.
    S3: start at lexicographically smallest endpoint; walk the unique path.
    S4: output = N×1 column of cell colors along that path order.
    C4: licensed only when every training pair replays exact.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _majority(grid: Grid) -> int:
    return Counter(cell for row in grid for cell in row).most_common(1)[0][0]


def path_column_unroll(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    height, width = len(grid), len(grid[0])
    bg = _majority(grid)
    cells = [(r, c) for r in range(height) for c in range(width) if grid[r][c] != bg]
    if len(cells) < 2:
        return None
    cell_set = set(cells)

    def neighbors(r: int, c: int) -> List[Tuple[int, int]]:
        out: List[Tuple[int, int]] = []
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if (nr, nc) in cell_set:
                out.append((nr, nc))
        return out

    degrees = {p: len(neighbors(*p)) for p in cells}
    if any(d == 0 or d > 2 for d in degrees.values()):
        return None
    ends = [p for p, d in degrees.items() if d == 1]
    if len(ends) != 2:
        return None
    start = min(ends)
    path = [start]
    prev: Optional[Tuple[int, int]] = None
    cur = start
    while True:
        opts = [n for n in neighbors(*cur) if n != prev]
        if not opts:
            break
        nxt = opts[0]
        prev, cur = cur, nxt
        if cur in path:
            return None
        path.append(cur)
    if len(path) != len(cells):
        return None
    return [[grid[r][c]] for r, c in path]


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("path_column_unroll", path_column_unroll)]


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
            "engine": "s1_path_column_unroll",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_path_column_unroll",
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
    "path_column_unroll",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
