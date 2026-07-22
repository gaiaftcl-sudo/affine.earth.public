"""S1 marker-hole align crop (FoT).

Grammar (zoom_in_crop):
  Majority color = wall. Non-wall 4-connected components are holes.
  Canvas hole = the singleton-accent hole (exactly one nonzero cell).
  Rich hole = the hole with the most nonzero accents.
  Content = tight nonzero crop of the rich hole.
  Align content onto a canvas-sized zero grid so the shared marker color
  coincides with the canvas marker position.

Canonical close: AGI-2 test task 2f0c5170.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _find_holes(grid: Grid, wall: int) -> List[Dict[str, Any]]:
    h0, w0 = len(grid), len(grid[0])
    seen = [[False] * w0 for _ in range(h0)]
    holes: List[Dict[str, Any]] = []
    for r in range(h0):
        for c in range(w0):
            if grid[r][c] == wall or seen[r][c]:
                continue
            cells: List[Tuple[int, int]] = []
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h0
                        and 0 <= ny < w0
                        and not seen[nx][ny]
                        and grid[nx][ny] != wall
                    ):
                        seen[nx][ny] = True
                        q.append((nx, ny))
            rs = [x for x, _ in cells]
            cs = [y for _, y in cells]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            crop = [
                [grid[rr][cc] for cc in range(c0, c1 + 1)] for rr in range(r0, r1 + 1)
            ]
            accents = sum(1 for x, y in cells if grid[x][y] != 0)
            holes.append(
                {
                    "cells": cells,
                    "r0": r0,
                    "c0": c0,
                    "h": r1 - r0 + 1,
                    "w": c1 - c0 + 1,
                    "crop": crop,
                    "accents": accents,
                }
            )
    return holes


def _tight_crop(crop: Grid) -> Optional[Grid]:
    if not crop or not crop[0]:
        return None
    h0, w0 = len(crop), len(crop[0])
    rows = [r for r in range(h0) if any(crop[r][c] != 0 for c in range(w0))]
    cols = [c for c in range(w0) if any(crop[r][c] != 0 for r in range(h0))]
    if not rows or not cols:
        return None
    return [
        [crop[r][c] for c in range(cols[0], cols[-1] + 1)]
        for r in range(rows[0], rows[-1] + 1)
    ]


def make_marker_hole_align_crop() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        wall = Counter(c for row in inp for c in row).most_common(1)[0][0]
        holes = _find_holes(inp, wall)
        ones = [h for h in holes if h["accents"] == 1]
        richs = [h for h in holes if h["accents"] > 1]
        if not ones or not richs:
            return None
        canvas = ones[0]
        rich = max(richs, key=lambda h: h["accents"])
        content = _tight_crop(rich["crop"])
        if content is None:
            return None
        markers: List[Tuple[int, int, int]] = []
        for r, c in canvas["cells"]:
            v = inp[r][c]
            if v != 0:
                markers.append((r - canvas["r0"], c - canvas["c0"], v))
        if not markers:
            return None
        mr, mc, mcol = markers[0]
        ch, cw = len(content), len(content[0])
        cands = [
            (r, c)
            for r in range(ch)
            for c in range(cw)
            if content[r][c] == mcol
        ]
        th, tw = canvas["h"], canvas["w"]
        for cr, cc in cands:
            ro, co = mr - cr, mc - cc
            out = [[0] * tw for _ in range(th)]
            ok = True
            for r in range(ch):
                for c in range(cw):
                    rr, cc2 = ro + r, co + c
                    if 0 <= rr < th and 0 <= cc2 < tw:
                        out[rr][cc2] = content[r][c]
                    elif content[r][c] != 0:
                        ok = False
            if ok:
                return out
        return None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("marker_hole_align_crop", make_marker_hole_align_crop())]


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
            "engine": "s1_marker_hole_align_crop",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_marker_hole_align_crop",
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
