"""S2 marker-column period tile (FoT).

Grammar (same_canvas_rewrite):
  - Leftmost column has a top run of a marker color; its length is the period.
  - Below the first all-zero content row, tile the period motif into empty
    content columns (marker column stays 0 in the fill region).

Canonical close: AGI-2 test task 12422b43.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def marker_col_period_tile(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    if w < 2:
        return None
    nz = [inp[r][0] for r in range(h) if inp[r][0] != 0]
    if not nz:
        return None
    marker = Counter(nz).most_common(1)[0][0]
    period = 0
    for r in range(h):
        if inp[r][0] == marker:
            period += 1
        else:
            break
    if period < 1:
        return None
    first_empty: Optional[int] = None
    for r in range(h):
        if all(inp[r][c] == 0 for c in range(1, w)):
            first_empty = r
            break
    if first_empty is None:
        return None
    out = [list(row) for row in inp]
    for r in range(first_empty, h):
        src = inp[(r - first_empty) % period]
        for c in range(1, w):
            out[r][c] = src[c]
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    if not train:
        return []
    for ex in train:
        inp, out = ex["input"], ex["output"]
        if not inp or not out or len(inp) != len(out) or len(inp[0]) != len(out[0]):
            return []

    def _xf(grid: Grid) -> Optional[Grid]:
        return marker_col_period_tile(grid)

    return [("marker_col_period_tile", _xf)]


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
            "engine": "s2_marker_col_period_tile",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_marker_col_period_tile",
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
    "marker_col_period_tile",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
