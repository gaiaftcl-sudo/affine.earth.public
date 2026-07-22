"""S2 column marks bottom pyramid (FoT).

Grammar (same_canvas_rewrite):
  Non-background cells lie on one vertical column. Clear the canvas, then restack
  at the bottom centered on that column:
    - one color: odd-width pyramid rows (1,3,5,...) from the bottom;
    - multiple colors: one row per color (width = count), top-to-bottom in first
      appearance order, sitting on the bottom rows.

Canonical close: AGI-2 test task 3d6c6e23.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_col_marks_bottom_pyramid(bg: int = 0) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        order: List[int] = []
        counts: Counter = Counter()
        col_sum = 0
        n = 0
        for r in range(h):
            for c in range(w):
                v = inp[r][c]
                if v == bg:
                    continue
                if v not in counts:
                    order.append(v)
                counts[v] += 1
                col_sum += c
                n += 1
        if n == 0 or not order:
            return None
        col = int(round(col_sum / n))
        out = [[bg] * w for _ in range(h)]
        if len(order) == 1:
            color = order[0]
            total = counts[color]
            widths: List[int] = []
            s = 0
            k = 1
            while s + k <= total:
                widths.append(k)
                s += k
                k += 2
            rem = total - s
            r = h - 1
            for width in reversed(widths):
                start = col - width // 2
                for c in range(start, start + width):
                    if 0 <= c < w:
                        out[r][c] = color
                r -= 1
            if rem:
                start = col - rem // 2
                for c in range(start, start + rem):
                    if 0 <= c < w:
                        out[r][c] = color
        else:
            nrows = len(order)
            r0 = h - nrows
            for i, color in enumerate(order):
                width = counts[color]
                start = col - width // 2
                for c in range(start, start + width):
                    if 0 <= c < w:
                        out[r0 + i][c] = color
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("col_marks_bottom_pyramid", make_col_marks_bottom_pyramid())]


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
            "engine": "s2_col_marks_bottom_pyramid",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, _ = exact[0]
    passed = len(train)
    return {
        "engine": "s2_col_marks_bottom_pyramid",
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
