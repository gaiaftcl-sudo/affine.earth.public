"""S2 border-mark period stamp (FoT).

Grammar (same_canvas_rewrite):
  Background is 8; one mark color C forms a single component touching the
  canvas border.
  - Touches exactly one side: paint length-|C| bars on the two perpendicular
    borders, aligned opposite the touched side. If the mark is a short bar on
    the left, also stamp period-2|C| repeats of length-|C| on top/bottom/right.
  - Touches a corner (two adjacent sides): H-flip (or V-flip) the mark onto the
    opposite corner side and paint a centered length-|C| bar on the far border.

Canonical close: AGI-2 test task 30f42897.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_border_mark_period_stamp(bg: int = 8) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        cnt = Counter(v for row in inp for v in row if v != bg)
        if len(cnt) != 1:
            return None
        color = next(iter(cnt))
        marks = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == color]
        if not marks:
            return None
        L = len(marks)
        touch_t = any(r == 0 for r, _ in marks)
        touch_b = any(r == h - 1 for r, _ in marks)
        touch_l = any(c == 0 for _, c in marks)
        touch_r = any(c == w - 1 for _, c in marks)
        n_touch = sum((touch_t, touch_b, touch_l, touch_r))
        out = [row[:] for row in inp]
        if n_touch == 1:
            if touch_r:
                for c in range(L):
                    out[0][c] = color
                    out[h - 1][c] = color
                return out
            if touch_l:
                # Single-side left: period stamps on the other three borders.
                period = 2 * L
                for start in range(1, w - 1, period):
                    for c in range(start, min(start + L, w - 1)):
                        out[0][c] = color
                for start in range(0, w, period):
                    for c in range(start, min(start + L, w)):
                        out[h - 1][c] = color
                for start in range(1, h - 1, period):
                    for r in range(start, min(start + L, h - 1)):
                        out[r][w - 1] = color
                return out
            if touch_t:
                for r in range(L):
                    out[r][0] = color
                    out[r][w - 1] = color
                return out
            if touch_b:
                for r in range(h - L, h):
                    out[r][0] = color
                    out[r][w - 1] = color
                return out
        if n_touch == 2:
            if touch_t and touch_l:
                for r, c in marks:
                    out[r][w - 1 - c] = color
                c0 = (w - L) // 2
                for c in range(c0, c0 + L):
                    out[h - 1][c] = color
                return out
            if touch_t and touch_r:
                for r, c in marks:
                    out[r][w - 1 - c] = color
                c0 = (w - L) // 2
                for c in range(c0, c0 + L):
                    out[h - 1][c] = color
                return out
            if touch_b and touch_l:
                for r, c in marks:
                    out[h - 1 - r][c] = color
                c0 = (w - L) // 2
                for c in range(c0, c0 + L):
                    out[0][c] = color
                return out
            if touch_b and touch_r:
                for r, c in marks:
                    out[h - 1 - r][w - 1 - c] = color
                c0 = (w - L) // 2
                for c in range(c0, c0 + L):
                    out[0][c] = color
                return out
        return None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("border_mark_period_stamp", make_border_mark_period_stamp())]


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
            "engine": "s2_border_mark_period_stamp",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_border_mark_period_stamp",
        "train_replay": f"{passed}/{len(train)}",
        "perfect": passed == len(train) and len(train) > 0,
        "passed": passed,
        "total": len(train),
        "licensed_transforms": [n for n, _ in exact],
        "primary_transform": name,
    }


def solve_task(task: Dict[str, Any]) -> Optional[List[Dict[str, Grid]]]:
    if not train_replay(task)["perfect"]:
        return None
    _, transform = exact_candidates(task["train"])[0]
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
