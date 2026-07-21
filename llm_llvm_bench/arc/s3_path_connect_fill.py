"""Batch FoT engine for eval task 6e453dd6.

Grammar family owned here:
  path_connect_fill (canonical: eval task 6e453dd6)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 6e453dd6). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def path_connect_fill(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


import json, sys
from collections import deque

def _solve(grid):
    rows, cols = len(grid), len(grid[0])
    g = [row[:] for row in grid]
    bg = 6
    
    white_col = None
    for c in range(cols):
        if all(g[r][c] == 5 for r in range(rows)):
            white_col = c
            break
    
    target_right = white_col - 1
    
    visited = [[False]*cols for _ in range(rows)]
    components = []
    for r in range(rows):
        for c in range(cols):
            if g[r][c] != 0 or visited[r][c]:
                continue
            comp = []
            q = deque([(r, c)])
            while q:
                cr, cc = q.popleft()
                if visited[cr][cc]:
                    continue
                visited[cr][cc] = True
                comp.append((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc] and g[nr][nc] == 0:
                        q.append((nr, nc))
            components.append(comp)
    
    for r in range(rows):
        for c in range(cols):
            if g[r][c] == 0:
                g[r][c] = bg
    
    for comp in components:
        max_col = max(c for r, c in comp)
        shift = target_right - max_col
        
        row_cols = {}
        for r, c in comp:
            nc = c + shift
            if 0 <= nc < cols:
                g[r][nc] = 0
                row_cols.setdefault(r, set()).add(nc)
        
        for r, col_set in row_cols.items():
            left, right = min(col_set), max(col_set)
            if right == target_right:
                has_gap = any(c not in col_set for c in range(left, right + 1))
                if has_gap:
                    for c in range(white_col + 1, cols):
                        g[r][c] = 2
    
    return g



def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("path_connect_fill", path_connect_fill)]


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
            "engine": "s3_path_connect_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_path_connect_fill",
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
    "path_connect_fill",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
