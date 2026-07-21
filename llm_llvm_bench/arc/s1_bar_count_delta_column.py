"""S1 bar-count delta column (FoT).

Grammar (same_canvas): let na = count(color a), nb = count(color b).
Paint `height = |na - nb|` cells of `paint` bottom-aligned in column w-2
(second-from-right), leaving the rest of the canvas unchanged.

Canonical close: AGI-2 test task 37ce87bb (a=8, b=2, paint=5, bg=7).
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def bar_delta_column(
    inp: Grid, a: int, b: int, paint: int, col_from_right: int = 2
) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    if w < col_from_right:
        return None
    na = sum(v == a for row in inp for v in row)
    nb = sum(v == b for row in inp for v in row)
    height = abs(na - nb)
    if height > h:
        return None
    out = [list(row) for row in inp]
    c = w - col_from_right
    for i in range(height):
        out[h - 1 - i][c] = paint
    return out


def _learn(train: Sequence[Dict[str, Any]]) -> Optional[Tuple[int, int, int, int]]:
    for a in range(0, 10):
        for b in range(0, 10):
            if a == b:
                continue
            for paint in range(0, 10):
                for col_from_right in (1, 2, 3):
                    if all(
                        bar_delta_column(ex["input"], a, b, paint, col_from_right)
                        == ex["output"]
                        for ex in train
                    ):
                        return a, b, paint, col_from_right
    return None


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    params = _learn(train)
    if params is None:
        return []
    a, b, paint, col_from_right = params

    def _xf(grid: Grid) -> Optional[Grid]:
        return bar_delta_column(grid, a, b, paint, col_from_right)

    return [(f"bar_delta_a{a}_b{b}_p{paint}_cfr{col_from_right}", _xf)]


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
            "engine": "s1_bar_count_delta_column",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_bar_count_delta_column",
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
    "bar_delta_column",
    "exact_candidates",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
