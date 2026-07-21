"""Batch FoT engine for eval task 65b59efc.

Grammar family owned here:
  symmetric_recolor (canonical: eval task 65b59efc)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 65b59efc). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def symmetric_recolor(grid: Grid) -> Optional[Grid]:
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
    
    # Find separator columns from row 0 (⬜ = 5)
    sep_cols = sorted(c for c in range(C) if grid[0][c] == 5)
    
    # Column groups
    col_groups = []
    prev = -1
    for sc in sep_cols:
        if sc > prev + 1:
            col_groups.append(list(range(prev + 1, sc)))
        prev = sc
    if prev < C - 1:
        col_groups.append(list(range(prev + 1, C)))
    
    # Find separator rows (rows with > half ⬜ in the active grid area)
    active_C = (sep_cols[-1] + 1) if sep_cols else C
    sep_rows = sorted(r for r in range(R) if sum(1 for c in range(active_C) if grid[r][c] == 5) > active_C // 2)
    
    # Row groups
    row_groups = []
    prev = -1
    for sr in sep_rows:
        if sr > prev + 1:
            row_groups.append(list(range(prev + 1, sr)))
        prev = sr
    if prev < R - 1:
        row_groups.append(list(range(prev + 1, R)))
    
    template_rows = row_groups[0]
    pointer_rows = row_groups[1]
    dot_rows = row_groups[2]
    
    tile_h = len(template_rows)
    tile_w = len(col_groups[0])
    n_tiles = len(col_groups)
    
    # Extract templates: color -> pattern offsets
    templates = {}
    template_colors = []
    for j, cg in enumerate(col_groups):
        color = None
        pattern = []
        for ri, r in enumerate(template_rows):
            for ci, c in enumerate(cg):
                v = grid[r][c]
                if v != 0:
                    pattern.append((ri, ci))
                    if color is None:
                        color = v
        templates[color] = pattern
        template_colors.append(color)
    
    # Extract dots per column group
    dots = {}
    for j, cg in enumerate(col_groups):
        for r in dot_rows:
            for c in cg:
                v = grid[r][c]
                if v != 0:
                    dots[j] = v
                    break
            if j in dots:
                break
    
    # Map template color -> output color
    color_map = {tc: dots.get(j, 0) for j, tc in enumerate(template_colors)}
    
    # Parse pointer tiles: non-0 cells define output tile positions
    output_tiles = {}
    for j, cg in enumerate(col_groups):
        for ri, r in enumerate(pointer_rows):
            for ci, c in enumerate(cg):
                v = grid[r][c]
                if v != 0 and v in templates:
                    output_tiles[(ri, ci)] = (templates[v], color_map[v])
    
    # Build output: pointer tile is tile_h x tile_w, each position is a tile
    out = [[0] * (tile_w * tile_w) for _ in range(tile_h * tile_h)]
    for (ti, tj), (pattern, color) in output_tiles.items():
        br, bc = ti * tile_h, tj * tile_w
        for dr, dc in pattern:
            out[br + dr][bc + dc] = color
    
    return out



def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("symmetric_recolor", symmetric_recolor)]


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
            "engine": "s2_symmetric_recolor",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_symmetric_recolor",
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
    "symmetric_recolor",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
