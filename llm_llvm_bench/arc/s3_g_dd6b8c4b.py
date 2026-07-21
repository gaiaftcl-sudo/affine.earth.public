"""Batch FoT engine for eval task dd6b8c4b.

Grammar family owned here:
  g_dd6b8c4b (canonical: eval task dd6b8c4b)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · dd6b8c4b). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_dd6b8c4b(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


#!/usr/bin/env python3
"""dd6b8c4b solver: Maroon dots migrate into 3x3 green ring with red center.

Rule:
1. Find 3x3 green(3) ring with red(2) center
2. Flood fill from ring through non-purple(6) cells to find reachable maroon(9) dots
3. N = min(reachable_count, 9)
4. Fill N ring cells with maroon in order: T, TL, TR, L, R, center, BL, BR, B
5. Remove the N nearest maroon dots (by BFS discovery order from ring)
"""
import json, sys
from collections import deque

def solve(grid):
    rows, cols = len(grid), len(grid[0])
    out = [r[:] for r in grid]
    
    # Find 3x3 green ring with red center
    cr, cc = -1, -1
    for r in range(1, rows-1):
        for c in range(1, cols-1):
            if grid[r][c] == 2:  # red center
                # Check 8 neighbors for green
                greens = sum(1 for dr in [-1,0,1] for dc in [-1,0,1] 
                           if (dr,dc)!=(0,0) and grid[r+dr][c+dc]==3)
                if greens >= 4:  # at least 4 green neighbors
                    cr, cc = r, c
                    break
        if cr >= 0: break
    
    if cr < 0:
        return out
    
    # Ring cell positions (relative to center)
    ring_cells = set()
    for dr in [-1,0,1]:
        for dc in [-1,0,1]:
            if (dr,dc) != (0,0) and grid[cr+dr][cc+dc] == 3:
                ring_cells.add((cr+dr, cc+dc))
    ring_cells.add((cr, cc))  # include center
    
    # Fill order: T, TL, TR, L, R, center, BL, BR, B
    fill_order = [
        (cr-1, cc),    # T
        (cr-1, cc-1),  # TL
        (cr-1, cc+1),  # TR
        (cr, cc-1),    # L
        (cr, cc+1),    # R
        (cr, cc),      # center
        (cr+1, cc-1),  # BL
        (cr+1, cc+1),  # BR
        (cr+1, cc),    # B
    ]
    
    # BFS from ring through non-purple cells to find reachable maroon dots
    visited = set()
    queue = deque()
    
    # Start BFS from ring cells and their immediate non-purple neighbors
    for r, c in ring_cells:
        visited.add((r, c))
        queue.append((r, c))
    
    maroon_found = []  # ordered by BFS discovery
    
    while queue:
        r, c = queue.popleft()
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0<=nr<rows and 0<=nc<cols and (nr,nc) not in visited:
                if grid[nr][nc] == 6:  # purple = wall
                    continue
                visited.add((nr, nc))
                if grid[nr][nc] == 9:  # maroon found
                    maroon_found.append((nr, nc))
                queue.append((nr, nc))
    
    # N = min(reachable maroon, 9)
    N = min(len(maroon_found), 9)
    
    # Fill N ring cells with maroon
    for i in range(N):
        fr, fc = fill_order[i]
        out[fr][fc] = 9
    
    # Remove N nearest maroon dots (BFS order = nearest first)
    for i in range(N):
        mr, mc = maroon_found[i]
        out[mr][mc] = 7  # replace with orange background
    
    return out

if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        task = json.load(f)
    for i, ex in enumerate(task['train']):
        result = solve(ex['input'])
        expected = ex['output']
        match = result == expected
        print(f"Train {i}: {'PASS ✓' if match else 'FAIL ✗'}")
        if not match:
            for r in range(len(expected)):
                for c in range(len(expected[0])):
                    if result[r][c] != expected[r][c]:
                        print(f"  ({r},{c}): got {result[r][c]} expected {expected[r][c]}")



def _solve(grid: Grid):
    return solve(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_dd6b8c4b", g_dd6b8c4b)]


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
            "engine": "s3_g_dd6b8c4b",
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
        "engine": "s3_g_dd6b8c4b",
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
    "g_dd6b8c4b",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
