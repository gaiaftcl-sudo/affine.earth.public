"""S2 same-color axis link (FoT).

Grammar (same_canvas_rewrite):
  For each nonzero color, connect every pair of cells that share a row
  or a column by filling the open segment between them with that color.

Canonical close: AGI-2 test task 070dd51e.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def same_color_axis_link(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    by_color: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
    for r in range(h):
        for c in range(w):
            if inp[r][c] != 0:
                by_color[inp[r][c]].append((r, c))
    out = [list(row) for row in inp]
    for col, pts in by_color.items():
        if len(pts) < 2:
            continue
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                (r1, c1), (r2, c2) = pts[i], pts[j]
                if r1 == r2:
                    for c in range(min(c1, c2) + 1, max(c1, c2)):
                        if out[r1][c] == 0:
                            out[r1][c] = col
                elif c1 == c2:
                    for r in range(min(r1, r2) + 1, max(r1, r2)):
                        if out[r][c1] == 0:
                            out[r][c1] = col
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("same_color_axis_link", same_color_axis_link)]


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
            "engine": "s2_same_color_axis_link",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_same_color_axis_link",
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
    "same_color_axis_link",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
