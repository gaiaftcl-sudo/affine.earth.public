"""S1 vertical-half XOR crop (FoT).

Grammar (zoom_in_crop): split the canvas into top/bottom halves of equal
height; emit a mid-height grid that is paint where exactly one half is
nonzero at that column (XOR), else 0.

Canonical close: AGI-2 test task 31d5ba1a (paint=6, 2 tests).
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def half_xor(inp: Grid, paint: int) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    if h % 2:
        return None
    mid = h // 2
    out: Grid = []
    for r in range(mid):
        row: List[int] = []
        for c in range(w):
            a = inp[r][c] != 0
            b = inp[r + mid][c] != 0
            row.append(paint if (a ^ b) else 0)
        out.append(row)
    return out


def _learn_paint(train: Sequence[Dict[str, Any]]) -> Optional[int]:
    for paint in range(1, 10):
        if all(half_xor(ex["input"], paint) == ex["output"] for ex in train):
            return paint
    return None


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    paint = _learn_paint(train)
    if paint is None:
        return []

    def _xf(grid: Grid) -> Optional[Grid]:
        return half_xor(grid, paint)

    return [(f"half_xor_paint{paint}", _xf)]


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
            "engine": "s1_half_xor_crop",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_half_xor_crop",
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
    "half_xor",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
