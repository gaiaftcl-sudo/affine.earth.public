"""S1 largest solid square color (FoT).

Grammar (zoom_in_crop):
  Find the nonzero color with the largest solid axis-aligned square in the
  input (tie-break: higher cell count). Emit a solid rectangle of that color
  whose shape is learned from train outputs (constant across demos).

Canonical close: AGI-2 test task 3194b014.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _max_solid_square(grid: Grid, color: int) -> int:
    h, w = len(grid), len(grid[0])
    best = 0
    for r0 in range(h):
        for c0 in range(w):
            for s in range(1, min(h - r0, w - c0) + 1):
                if all(
                    grid[r0 + i][c0 + j] == color for i in range(s) for j in range(s)
                ):
                    best = max(best, s)
                else:
                    break
    return best


def _learn_out_shape(train: Sequence[Dict[str, Any]]) -> Optional[Tuple[int, int]]:
    shapes = {(len(ex["output"]), len(ex["output"][0])) for ex in train}
    if len(shapes) != 1:
        return None
    return next(iter(shapes))


def make_square_color(oh: int, ow: int) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        cnt = Counter(c for row in inp for c in row if c)
        if not cnt:
            return None
        best: Optional[Tuple[Tuple[int, int], int]] = None
        for color in cnt:
            key = (_max_solid_square(inp, color), cnt[color])
            if best is None or key > best[0]:
                best = (key, color)
        assert best is not None
        col = best[1]
        return [[col] * ow for _ in range(oh)]

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    shape = _learn_out_shape(train)
    if shape is None:
        return []
    oh, ow = shape
    return [("largest_solid_square_color", make_square_color(oh, ow))]


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
            "engine": "s1_largest_solid_square_color",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_largest_solid_square_color",
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
    "submission_fragment",
    "train_replay",
]
