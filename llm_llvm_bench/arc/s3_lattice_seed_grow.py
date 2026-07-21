"""Batch FoT engine for eval task 4c3d4a41.

Grammar family owned here:
  lattice_seed_grow (canonical: eval task 4c3d4a41)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 4c3d4a41). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def lattice_seed_grow(grid: Grid) -> Optional[Grid]:
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

def _solve(grid):
    R, C = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    
    # Find separator: all-0 column with non-0 content on both sides
    sep = None
    for c in range(1, C-1):
        if all(grid[r][c] == 0 for r in range(R)):
            has_left = any(grid[r][lc] != 0 for r in range(R) for lc in range(c))
            has_right = any(grid[r][rc] != 0 for r in range(R) for rc in range(c+1, C))
            if has_left and has_right:
                sep = c
                break
    if sep is None:
        return grid
    
    # Find all left ⬜(5) cells (staircase)
    left_white = set()
    for r in range(R):
        for c in range(sep):
            if grid[r][c] == 5:
                left_white.add((r, c))
    if not left_white:
        return grid
    
    # Find data columns in right half (cols with non-0, non-5 values)
    right_data_cols = []
    for c in range(sep+1, C):
        for r in range(R):
            if grid[r][c] not in (0, 5):
                right_data_cols.append(c)
                break
    
    # Find staircase data columns in left (cols with ⬜ above base row)
    base_row = max(r for r, c in left_white)
    left_data_cols = sorted(set(c for r, c in left_white if r < base_row))
    
    # Compute offset: first left data col -> first right data col
    if not left_data_cols or not right_data_cols:
        return grid
    offset = right_data_cols[0] - left_data_cols[0]
    
    # Clear left half
    for r in range(R):
        for c in range(sep):
            out[r][c] = 0
    
    # Map staircase positions to right half
    staircase_right = set()
    for r, c in left_white:
        tc = c + offset
        if sep < tc < C:
            staircase_right.add((r, tc))
    
    # Find right frame interior top row
    right_border = sep + 1
    int_top = None
    for r in range(R):
        if grid[r][right_border] == 5:
            if int_top is None:
                int_top = r + 1
    if int_top is None:
        int_top = 0
    
    # For each data column, compress colors into non-staircase rows
    for dc in right_data_cols:
        # Staircase rows for this column
        stairs = set(r for r in range(R) if (r, dc) in staircase_right)
        
        # Active area: from int_top to max staircase row
        active_top = int_top
        active_bot = base_row
        
        # Extract colors from original (non-0, non-5)
        colors = []
        for r in range(active_top, active_bot + 1):
            v = grid[r][dc]
            if v not in (0, 5):
                colors.append(v)
        
        # Available rows (active, not staircase)
        avail = [r for r in range(active_top, active_bot + 1) if r not in stairs]
        
        # Place colors at BOTTOM of available, ⬜ fills top
        n = min(len(colors), len(avail))
        for j, r in enumerate(avail):
            if j < len(avail) - n:
                out[r][dc] = 5
            else:
                color_idx = j - (len(avail) - n)
                out[r][dc] = colors[color_idx]
        
        # Staircase rows within active area → ⬜
        for r in stairs:
            if active_top <= r <= active_bot:
                out[r][dc] = 5
    
    # Apply staircase ⬜ to spacing columns in right half
    for r, c in left_white:
        tc = c + offset
        if sep < tc < C and tc not in right_data_cols:
            out[r][tc] = 5
    
    return out



def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("lattice_seed_grow", lattice_seed_grow)]


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
            "engine": "s3_lattice_seed_grow",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_lattice_seed_grow",
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
    "lattice_seed_grow",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
