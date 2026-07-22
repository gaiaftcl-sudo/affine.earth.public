"""S2 marker corner-rect paint (FoT).

Grammar (same_canvas_rewrite):
  Locate the bbox of color-5 cells. Group non-{0,5} markers by color. Classify
  each group by centroid vs bbox center into a corner, then paint:
    top-left:     (r0..max_mr, c0..max_mc)
    top-right:    (r0..max_mr, min_mc..c1)
    bottom-left:  (min_mr..r1, c0..max_mc)
    bottom-right: (min_mr..r1, min_mc..c1)
  clipped to the 5-bbox. Output zeros outside the bbox; 5s fill the rest.

Canonical close: AGI-2 test task 1c02dbbe.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_marker_corner_rect_paint(fill: int = 5) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        fives = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == fill]
        if not fives:
            return None
        r0 = min(r for r, _ in fives)
        r1 = max(r for r, _ in fives)
        c0 = min(c for _, c in fives)
        c1 = max(c for _, c in fives)
        by: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
        for r in range(h):
            for c in range(w):
                v = inp[r][c]
                if v not in (0, fill):
                    by[v].append((r, c))
        if not by:
            return None
        out = [[0] * w for _ in range(h)]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = fill
        cr = (r0 + r1) / 2.0
        cc = (c0 + c1) / 2.0
        for col, pos in by.items():
            mr = sum(r for r, _ in pos) / len(pos)
            mc = sum(c for _, c in pos) / len(pos)
            mrs = [r for r, _ in pos]
            mcs = [c for _, c in pos]
            top = mr <= cr
            left = mc <= cc
            if top and left:
                rr0, rr1, cc0, cc1 = r0, max(mrs), c0, max(mcs)
            elif top and not left:
                rr0, rr1, cc0, cc1 = r0, max(mrs), min(mcs), c1
            elif (not top) and left:
                rr0, rr1, cc0, cc1 = min(mrs), r1, c0, max(mcs)
            else:
                rr0, rr1, cc0, cc1 = min(mrs), r1, min(mcs), c1
            rr0 = max(rr0, r0)
            rr1 = min(rr1, r1)
            cc0 = max(cc0, c0)
            cc1 = min(cc1, c1)
            if rr0 > rr1 or cc0 > cc1:
                return None
            for r in range(rr0, rr1 + 1):
                for c in range(cc0, cc1 + 1):
                    out[r][c] = col
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("marker_corner_rect_paint", make_marker_corner_rect_paint())]


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
            "engine": "s2_marker_corner_rect_paint",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_marker_corner_rect_paint",
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
