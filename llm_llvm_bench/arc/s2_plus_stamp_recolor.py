"""S2 plus-stamp recolor language game (FoT).

Grammar family owned here:
  plus_stamp_recolor (canonical: eval task 1818057f)
    S1: same canvas shape (in-place palette rewrite).
    S2: bipartite palette — majority = background; the other color = foreground.
    S3: every orthogonal plus of 5 foreground cells (center + N/E/S/W) is a stamp.
    S4: recolor each stamp cell to constant 8; other cells unchanged.
    C4: exact rewrite; licensed only when every training pair replays and ≥1 stamp.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_RECOLOR = 8


def plus_stamp_recolor(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    height, width = len(grid), len(grid[0])
    counts = Counter(cell for row in grid for cell in row)
    if len(counts) != 2:
        return None
    bg = counts.most_common(1)[0][0]
    fg = next(color for color in counts if color != bg)
    if _RECOLOR in counts:
        return None
    out = [list(row) for row in grid]
    stamps = 0
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != fg:
                continue
            if (
                grid[row - 1][col] == fg
                and grid[row + 1][col] == fg
                and grid[row][col - 1] == fg
                and grid[row][col + 1] == fg
            ):
                stamps += 1
                for rr, cc in (
                    (row, col),
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                ):
                    out[rr][cc] = _RECOLOR
    if stamps == 0:
        return None
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("plus_stamp_recolor", plus_stamp_recolor)]


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
            "engine": "s2_plus_stamp_recolor",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_plus_stamp_recolor",
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
    "plus_stamp_recolor",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
