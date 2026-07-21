"""Batch FoT engine for eval task dbff022c.

Grammar family owned here:
  g_dbff022c (canonical: eval task dbff022c)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · dbff022c). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_dbff022c(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


"""Solver for dbff022c — Frame Fill via Color Key"""
import json
from typing import List
from collections import deque

def solve(grid: List[List[int]]) -> List[List[int]]:
    rows, cols = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    
    # Find connected components of non-zero cells
    visited = set()
    components = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != 0 and (r,c) not in visited:
                comp = set()
                q = deque([(r,c)])
                visited.add((r,c))
                while q:
                    cr, cc = q.popleft()
                    comp.add((cr,cc))
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = cr+dr, cc+dc
                        if 0<=nr<rows and 0<=nc<cols and (nr,nc) not in visited and grid[nr][nc]!=0:
                            visited.add((nr,nc))
                            q.append((nr,nc))
                components.append(comp)
    
    # Key = component with most unique colors
    key_cells = max(components, key=lambda c: len(set(grid[r][c] for r,c in c)))
    
    # Parse key
    kr = [r for r,c in key_cells]
    kc = [c for r,c in key_cells]
    r0, r1, c0, c1 = min(kr), max(kr), min(kc), max(kc)
    krows, kcols = r1-r0+1, c1-c0+1
    
    forward = {}
    reverse = {}
    if krows == 2:  # column pairs (top→bottom)
        for c in range(c0, c1+1):
            if grid[r0][c] != 0 and grid[r1][c] != 0:
                forward[grid[r0][c]] = grid[r1][c]
                reverse[grid[r1][c]] = grid[r0][c]
    elif kcols == 2:  # row pairs (left→right)
        for r in range(r0, r1+1):
            if grid[r][c0] != 0 and grid[r][c1] != 0:
                forward[grid[r][c0]] = grid[r][c1]
                reverse[grid[r][c1]] = grid[r][c0]

    # Determine correct mapping direction by checking which key set
    # has more overlap with actual frame border colors in the grid
    frame_colors = set()
    for comp in components:
        if comp is not key_cells:
            for cr, cc in comp:
                frame_colors.add(grid[cr][cc])
    fwd_hits = len(frame_colors & set(forward.keys()))
    rev_hits = len(frame_colors & set(reverse.keys()))
    mapping = reverse if rev_hits > fwd_hits else forward
    
    # Flood fill from border to find exterior cells
    exterior = set()
    q = deque()
    for r in range(rows):
        for c in range(cols):
            if (r==0 or r==rows-1 or c==0 or c==cols-1) and grid[r][c]==0:
                exterior.add((r,c))
                q.append((r,c))
    while q:
        r, c = q.popleft()
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0<=nr<rows and 0<=nc<cols and (nr,nc) not in exterior and grid[nr][nc]==0:
                exterior.add((nr,nc))
                q.append((nr,nc))
    
    # Interior cells
    interior = [(r,c) for r in range(rows) for c in range(cols) 
                if grid[r][c]==0 and (r,c) not in exterior]
    
    # For each interior cell, find frame color (nearest non-zero non-key cell)
    for r, c in interior:
        neighbors = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0<=nr<rows and 0<=nc<cols and grid[nr][nc]!=0 and (nr,nc) not in key_cells:
                neighbors.append(grid[nr][nc])
        if not neighbors:
            vis = {(r,c)}
            bq = deque([(r,c)])
            while bq and not neighbors:
                br, bc = bq.popleft()
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = br+dr, bc+dc
                    if 0<=nr<rows and 0<=nc<cols and (nr,nc) not in vis:
                        vis.add((nr,nc))
                        if grid[nr][nc]!=0 and (nr,nc) not in key_cells:
                            neighbors.append(grid[nr][nc])
                        elif grid[nr][nc]==0 and (nr,nc) not in exterior:
                            bq.append((nr,nc))
        if neighbors:
            frame_color = max(set(neighbors), key=neighbors.count)
            if frame_color in mapping:
                out[r][c] = mapping[frame_color]
    
    return out

if __name__ == '__main__':
    import sys
    with open(sys.argv[1]) as f: task = json.load(f)
    for i, ex in enumerate(task['train']):
        result = solve(ex['input'])
        match = result == ex['output']
        print(f"Train {i}: {'PASS ✓' if match else 'FAIL ✗'}")
        if not match:
            diffs = [(r,c,result[r][c],ex['output'][r][c]) for r in range(len(result)) for c in range(len(result[0])) if result[r][c]!=ex['output'][r][c]]
            for r,c,g,e in diffs[:10]: print(f"  ({r},{c}): got {g} expected {e}")



def _solve(grid: Grid):
    return solve(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_dbff022c", g_dbff022c)]


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
            "engine": "s3_g_dbff022c",
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
        "engine": "s3_g_dbff022c",
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
    "g_dbff022c",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
