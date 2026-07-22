"""S2 bbox row triangle-shear (FoT).

Grammar (same_canvas_rewrite):
  Single non-zero color. Shear each object row horizontally by a period-4
  triangle wave [-1, 0, +1, 0]. Phase p = (2 - H) mod 4 where H is the
  object's row span, so the bottom row is unshifted.

Canonical close: AGI-2 test task 1c56ad9f.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_WAVE = (-1, 0, 1, 0)


def make_bbox_row_triangle_shear() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        nonzero = [v for row in inp for v in row if v]
        if not nonzero:
            return None
        color = Counter(nonzero).most_common(1)[0][0]
        if any(v not in (0, color) for row in inp for v in row):
            return None
        cells = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == color]
        if not cells:
            return None
        r0 = min(r for r, _ in cells)
        r1 = max(r for r, _ in cells)
        H = r1 - r0 + 1
        p = (2 - H) % 4
        out = [[0] * w for _ in range(h)]
        moved = False
        for r in range(r0, r1 + 1):
            sh = _WAVE[(r - r0 + p) % 4]
            for c in range(w):
                if inp[r][c] != color:
                    continue
                nc = c + sh
                if not (0 <= nc < w):
                    return None
                out[r][nc] = color
                if nc != c:
                    moved = True
        if not moved:
            return None
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("bbox_row_triangle_shear", make_bbox_row_triangle_shear())]


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
            "engine": "s2_bbox_row_triangle_shear",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_bbox_row_triangle_shear",
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
