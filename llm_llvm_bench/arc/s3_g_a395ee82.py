"""Batch FoT engine for eval task a395ee82.

Grammar family owned here:
  g_a395ee82 (canonical: eval task a395ee82)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · a395ee82). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_a395ee82(grid: Grid) -> Optional[Grid]:
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
from collections import Counter

def solve(grid):
    H = len(grid)
    W = len(grid[0])
    bg = Counter(grid[r][c] for r in range(H) for c in range(W)).most_common(1)[0][0]
    
    cells = {}
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg:
                cells[(r,c)] = grid[r][c]
    
    # Find connected components
    visited = set()
    components = []
    for (r,c) in cells:
        if (r,c) in visited: continue
        comp = []
        queue = [(r,c)]
        visited.add((r,c))
        while queue:
            cr,cc = queue.pop(0)
            comp.append((cr,cc))
            for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr,nc = cr+dr,cc+dc
                if (nr,nc) not in visited and (nr,nc) in cells:
                    visited.add((nr,nc))
                    queue.append((nr,nc))
        components.append(comp)
    
    # Multi-cell = shape, single = dots
    shape_cells = []
    dots = []
    for comp in components:
        if len(comp) > 1:
            shape_cells.extend(comp)
        else:
            dots.append(comp[0])
    
    # Shape color and bounding box
    shape_color = Counter(cells[(r,c)] for r,c in shape_cells).most_common(1)[0][0]
    min_r = min(r for r,c in shape_cells)
    max_r = max(r for r,c in shape_cells)
    min_c = min(c for r,c in shape_cells)
    max_c = max(c for r,c in shape_cells)
    shape_h = max_r - min_r + 1
    shape_w = max_c - min_c + 1
    
    # Shape pattern relative to (min_r, min_c)
    shape_pattern = []
    for (r,c) in shape_cells:
        shape_pattern.append((r - min_r, c - min_c))
    
    # Find dot center (same color as shape) and surrounding dots
    center_dot = None
    surround_dots = []
    for (r,c) in dots:
        if cells[(r,c)] == shape_color:
            center_dot = (r,c)
        else:
            surround_dots.append((r,c))
    
    surround_color = cells[surround_dots[0]] if surround_dots else shape_color
    
    # Dot spacing = min distance from center to any surrounding dot
    cr, cc = center_dot
    min_dist = min(abs(r-cr) + abs(c-cc) for r,c in surround_dots)
    dot_spacing = min_dist  # typically 2
    
    # Calculate offsets for each surrounding dot
    out = [[bg]*W for _ in range(H)]
    
    # Place copies
    for (dr, dc) in surround_dots:
        row_off = dr - cr
        col_off = dc - cc
        # Scale offsets
        scaled_row = round(row_off * shape_h / dot_spacing)
        scaled_col = round(col_off * shape_w / dot_spacing)
        
        new_r = min_r + scaled_row
        new_c = min_c + scaled_col
        
        for (pr, pc) in shape_pattern:
            nr, nc = new_r + pr, new_c + pc
            if 0 <= nr < H and 0 <= nc < W:
                out[nr][nc] = shape_color
    
    # Place center shape in surround color
    for (pr, pc) in shape_pattern:
        nr, nc = min_r + pr, min_c + pc
        if 0 <= nr < H and 0 <= nc < W:
            out[nr][nc] = surround_color
    
    return out

if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        task = json.load(f)
    for i, ex in enumerate(task['train']):
        result = solve(ex['input'])
        match = result == ex['output']
        print(f"Train {i}: {'PASS' if match else 'FAIL'}")
        if not match:
            import numpy as np
            r = np.array(result)
            e = np.array(ex['output'])
            diffs = np.argwhere(r != e)
            print(f"  {len(diffs)} diffs")
            for d in diffs[:10]:
                print(f"  ({d[0]},{d[1]}): got {r[d[0],d[1]]}, exp {e[d[0],d[1]]}")



def _solve(grid: Grid):
    return solve(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_a395ee82", g_a395ee82)]


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
            "engine": "s3_g_a395ee82",
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
        "engine": "s3_g_a395ee82",
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
    "g_a395ee82",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
