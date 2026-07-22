"""S2 marker-column template bands (FoT).

Grammar (same_canvas_rewrite):
  Find the marker column (most 8s). Template rows are those with a 1 in the
  marker column and a dominant non-7 fill color. Between consecutive templates:
  if colors differ and the gap is even, the midpoint row becomes all-1s;
  otherwise the floor-midpoint splits territories. Template rows become all-1s
  with an 8 at the marker column; other rows in a territory fill with that
  template's color and a 1 at the marker column.
  Licensed only on perfect train replay.

Canonical close: AGI-2 test task 332202d5.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _marker_col_template_bands(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    col8: Counter = Counter()
    for r in range(h):
        for c in range(w):
            if inp[r][c] == 8:
                col8[c] += 1
    if not col8:
        return None
    mc = col8.most_common(1)[0][0]
    templates: List[Tuple[int, int]] = []
    for r in range(h):
        row = inp[r]
        if row[mc] != 1:
            continue
        cols = Counter(row[c] for c in range(w) if c != mc)
        if not cols:
            continue
        color = cols.most_common(1)[0][0]
        if color != 7:
            templates.append((r, color))
    if not templates:
        return None
    templates.sort()
    row_color: List[Optional[int]] = [None] * h
    row_kind = ["fill"] * h
    ts = templates
    for i, (tr, col) in enumerate(ts):
        row_kind[tr] = "sep"
        if i == 0:
            left = 0
        else:
            prev_r, prev_c = ts[i - 1]
            gap = tr - prev_r
            mid = (prev_r + tr) // 2
            if prev_c != col and gap % 2 == 0:
                row_kind[mid] = "all1"
                left = mid + 1
            else:
                left = mid + 1
        if i == len(ts) - 1:
            right = h - 1
        else:
            next_r, next_c = ts[i + 1]
            gap = next_r - tr
            mid = (tr + next_r) // 2
            if col != next_c and gap % 2 == 0:
                right = mid - 1
            else:
                right = mid
        for r in range(left, right + 1):
            if row_kind[r] == "fill":
                row_color[r] = col
    out: Grid = [[7] * w for _ in range(h)]
    for r in range(h):
        if row_kind[r] == "all1":
            out[r] = [1] * w
        elif row_kind[r] == "sep":
            out[r] = [1] * w
            out[r][mc] = 8
        else:
            col = row_color[r]
            if col is None:
                return None
            out[r] = [col] * w
            out[r][mc] = 1
    return out


def make_marker_col_template_bands() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _marker_col_template_bands(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("marker_col_template_bands", make_marker_col_template_bands())]


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
            "engine": "s2_marker_col_template_bands",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_marker_col_template_bands",
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
