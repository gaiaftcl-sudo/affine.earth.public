"""S2 marker-count expand fives (FoT).

Grammar (same_canvas_rewrite):
  Non-{0,5} cells are markers of one color. On every row that contains 5s,
  expand the 5-segment left by the number of markers left of it and right by
  the number of markers right of it (markers inside the span become 5).
  Same rule on columns (above/below). Then clear all original marker cells
  that were not painted 5.

Canonical close: AGI-2 test task 4093f84a.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_marker_count_expand_fives() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        marks = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if inp[r][c] not in (0, 5)
        ]
        if not marks:
            return None
        if len({inp[r][c] for r, c in marks}) != 1:
            return None
        if not any(inp[r][c] == 5 for r in range(h) for c in range(w)):
            return None
        out = [list(row) for row in inp]
        for r, c in marks:
            out[r][c] = 0
        five_rows: Dict[int, List[int]] = defaultdict(list)
        five_cols: Dict[int, List[int]] = defaultdict(list)
        for r in range(h):
            for c in range(w):
                if inp[r][c] == 5:
                    five_rows[r].append(c)
                    five_cols[c].append(r)
        marks_by_row: Dict[int, List[int]] = defaultdict(list)
        marks_by_col: Dict[int, List[int]] = defaultdict(list)
        for r, c in marks:
            marks_by_row[r].append(c)
            marks_by_col[c].append(r)
        for r, cols in five_rows.items():
            cols = sorted(cols)
            c0, c1 = cols[0], cols[-1]
            left = sum(1 for c in marks_by_row.get(r, []) if c < c0)
            right = sum(1 for c in marks_by_row.get(r, []) if c > c1)
            for k in range(1, left + 1):
                if c0 - k >= 0:
                    out[r][c0 - k] = 5
            for k in range(1, right + 1):
                if c1 + k < w:
                    out[r][c1 + k] = 5
            for c in marks_by_row.get(r, []):
                if c0 <= c <= c1:
                    out[r][c] = 5
        for c, rows in five_cols.items():
            rows = sorted(rows)
            r0, r1 = rows[0], rows[-1]
            above = sum(1 for r in marks_by_col.get(c, []) if r < r0)
            below = sum(1 for r in marks_by_col.get(c, []) if r > r1)
            for k in range(1, above + 1):
                if r0 - k >= 0:
                    out[r0 - k][c] = 5
            for k in range(1, below + 1):
                if r1 + k < h:
                    out[r1 + k][c] = 5
            for r in marks_by_col.get(c, []):
                if r0 <= r <= r1:
                    out[r][c] = 5
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("marker_count_expand_fives", make_marker_count_expand_fives())]


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
            "engine": "s2_marker_count_expand_fives",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_marker_count_expand_fives",
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
