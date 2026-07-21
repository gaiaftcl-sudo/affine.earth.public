"""Batch FoT engine for eval task da515329.

Grammar family owned here:
  g_da515329 (canonical: eval task da515329)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · da515329). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_da515329(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


"""
ARC-AGI puzzle da515329 — Spiral/maze pattern solver.

Input: Grid with a cross/plus of 8s (center=0, arms=8) of arm length L.
Output: Concentric rectangular spiral of 8s and 0s radiating from the cross.

Pattern rules (Chebyshev-distance rings from center):
  d=0: center cell is 0.
  d < max(2,L): alternating checkerboard — value=8 iff position_parity == d_parity.
  d >= max(2,L): spiral zone — each ring is mostly one value (base) with
      minority "gaps" at specific positions within each quadrant of 2d elements.
      The gap offsets follow a fixed formula based on L.
"""

import json
import sys


def transform(grid: list[list[int]]) -> list[list[int]]:
    H = len(grid)
    W = len(grid[0])

    # Locate the cross: find center (cy, cx) and arm length L
    cells8 = [(r, c) for r in range(H) for c in range(W) if grid[r][c] == 8]
    rows8 = [r for r, c in cells8]
    cols8 = [c for r, c in cells8]
    cy = (min(rows8) + max(rows8)) // 2
    cx = (min(cols8) + max(cols8)) // 2
    L = cy - min(rows8)

    S = max(2, L)                   # first spiral-zone ring distance
    gap_parity = (S + 1) % 2       # parity of minority-offset positions
    n_gaps = max(1, L - 1)         # minority positions per quadrant
    n_front = (L + 1) // 2         # ceil(L/2): gaps taken from front
    n_back = n_gaps - n_front      # gaps taken from back

    out = [[0] * W for _ in range(H)]

    for r in range(H):
        for c in range(W):
            dr = r - cy
            dc = c - cx
            d = max(abs(dr), abs(dc))

            if d == 0:
                out[r][c] = 0
                continue

            # Position along ring d (clockwise from top-left corner)
            if dr == -d:
                p = dc + d
            elif dc == d:
                p = 3 * d + dr
            elif dr == d:
                p = 5 * d - dc
            else:
                p = 7 * d - dr

            if d < S:
                # Alternating zone: checkerboard matching d's parity
                out[r][c] = 8 if p % 2 == d % 2 else 0
            else:
                # Spiral zone
                quad_offset = p % (2 * d)

                is_gap = False
                if quad_offset % 2 == gap_parity:
                    # Index among same-parity offsets within the quadrant
                    idx = quad_offset // 2 if gap_parity == 0 else (quad_offset - 1) // 2
                    if idx < n_front or idx >= d - n_back:
                        is_gap = True

                if (d - S) % 2 == 0:
                    out[r][c] = 0 if is_gap else 8   # base=8, minority=0
                else:
                    out[r][c] = 8 if is_gap else 0   # base=0, minority=8

    return out



def _solve(grid: Grid):
    return transform(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_da515329", g_da515329)]


def exact_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    out: List[Tuple[str, Transform]] = []
    for name, transform in named_candidates():
        if all(transform(ex["input"]) == ex["output"] for ex in train):
            out.append((name, transform))
    return out


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    train = task.get("train", [])
    exact = exact_candidates(train)
    if not exact:
        return {
            "engine": "s3_g_da515329",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
            "primary_transform": None,
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_g_da515329",
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
    "g_da515329",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
