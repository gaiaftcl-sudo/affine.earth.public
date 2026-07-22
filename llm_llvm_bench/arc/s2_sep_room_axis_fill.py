"""S2 separator-room axis fill (FoT).

Grammar (same_canvas_rewrite):
  Full separator rows/cols of one color carve a lattice of solid rooms.
  Each non-separator color occupies one or more solid rooms.
  For every color:
    - on each room-row with ≥2 occupied rooms, fill all rooms between
    - on each room-col with ≥2 occupied rooms, fill all rooms between
  Singleton rooms stay. Licensed only on perfect train replay.

Canonical close: AGI-2 test task 06df4c85.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_sep_room_axis_fill() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        sep_rows = [
            r
            for r in range(h)
            if len(set(inp[r])) == 1 and inp[r][0] != 0
        ]
        if len(sep_rows) < 2:
            return None
        sep = inp[sep_rows[0]][0]
        if any(inp[r][0] != sep for r in sep_rows):
            return None
        sep_cols = [
            c for c in range(w) if all(inp[r][c] == sep for r in range(h))
        ]
        if len(sep_cols) < 2:
            return None

        bounds_r = [-1] + sep_rows + [h]
        rb = [(a + 1, b - 1) for a, b in zip(bounds_r, bounds_r[1:]) if b - a > 1]
        bounds_c = [-1] + sep_cols + [w]
        cb = [(a + 1, b - 1) for a, b in zip(bounds_c, bounds_c[1:]) if b - a > 1]
        if not rb or not cb:
            return None

        color_rooms: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
        for ri, (r0, r1) in enumerate(rb):
            for ci, (c0, c1) in enumerate(cb):
                cols = {
                    inp[r][c]
                    for r in range(r0, r1 + 1)
                    for c in range(c0, c1 + 1)
                    if inp[r][c] and inp[r][c] != sep
                }
                if not cols:
                    continue
                if len(cols) != 1:
                    return None
                col = next(iter(cols))
                if not all(
                    inp[r][c] == col
                    for r in range(r0, r1 + 1)
                    for c in range(c0, c1 + 1)
                ):
                    return None
                color_rooms[col].append((ri, ci))

        if not color_rooms:
            return None

        painted: Dict[Tuple[int, int], int] = {}
        for col, rooms in color_rooms.items():
            by_r: Dict[int, List[int]] = defaultdict(list)
            by_c: Dict[int, List[int]] = defaultdict(list)
            for ri, ci in rooms:
                by_r[ri].append(ci)
                by_c[ci].append(ri)
                key = (ri, ci)
                if key in painted and painted[key] != col:
                    return None
                painted[key] = col
            for ri, cols in by_r.items():
                if len(cols) >= 2:
                    for ci in range(min(cols), max(cols) + 1):
                        key = (ri, ci)
                        if key in painted and painted[key] != col:
                            return None
                        painted[key] = col
            for ci, rows in by_c.items():
                if len(rows) >= 2:
                    for ri in range(min(rows), max(rows) + 1):
                        key = (ri, ci)
                        if key in painted and painted[key] != col:
                            return None
                        painted[key] = col

        out = [row[:] for row in inp]
        changed = False
        for (ri, ci), col in painted.items():
            r0, r1 = rb[ri]
            c0, c1 = cb[ci]
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if out[r][c] != col:
                        changed = True
                    out[r][c] = col
        return out if changed or painted else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("sep_room_axis_fill", make_sep_room_axis_fill())]


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
            "engine": "s2_sep_room_axis_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_sep_room_axis_fill",
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
