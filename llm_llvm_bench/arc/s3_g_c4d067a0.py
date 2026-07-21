"""Batch FoT engine for eval task c4d067a0.

Grammar family owned here:
  g_c4d067a0 (canonical: eval task c4d067a0)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · c4d067a0). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_c4d067a0(grid: Grid) -> Optional[Grid]:
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
from collections import deque, Counter

def solve(grid):
    rows, cols = len(grid), len(grid[0])
    g = [row[:] for row in grid]
    
    counts = Counter()
    for row in g:
        counts.update(row)
    bg = counts.most_common(1)[0][0]
    
    visited = [[False]*cols for _ in range(rows)]
    components = []
    for r in range(rows):
        for c in range(cols):
            if g[r][c] == bg or visited[r][c]:
                continue
            comp = []
            q = deque([(r,c)])
            while q:
                cr, cc = q.popleft()
                if visited[cr][cc]: continue
                visited[cr][cc] = True
                comp.append((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc] and g[nr][nc] != bg:
                        q.append((nr,nc))
            components.append(comp)
    
    markers = []
    blocks = []
    for comp in components:
        if len(comp) == 1:
            r, c = comp[0]
            markers.append((r, c, g[r][c]))
        else:
            min_r = min(r for r,c in comp)
            min_c = min(c for r,c in comp)
            max_r = max(r for r,c in comp)
            max_c = max(c for r,c in comp)
            color = g[comp[0][0]][comp[0][1]]
            blocks.append((min_r, min_c, max_r-min_r+1, max_c-min_c+1, color))
    
    if not markers or not blocks:
        return g
    
    t_rows = sorted(set(r for r,c,v in markers))
    t_cols = sorted(set(c for r,c,v in markers))
    t_row_step = t_rows[1] - t_rows[0] if len(t_rows) > 1 else 2
    t_col_step = t_cols[1] - t_cols[0] if len(t_cols) > 1 else 2
    
    tr_idx = {r: i for i, r in enumerate(t_rows)}
    tc_idx = {c: i for i, c in enumerate(t_cols)}
    template = {}
    for r, c, v in markers:
        ri, ci = tr_idx[r], tc_idx[c]
        template[(ri, ci)] = v
    
    num_tr = len(t_rows)
    num_tc = len(t_cols)
    
    block_h = blocks[0][2]
    block_w = blocks[0][3]
    
    b_col_starts = sorted(set(b[1] for b in blocks))
    b_col_step = b_col_starts[1] - b_col_starts[0] if len(b_col_starts) > 1 else block_w + 1
    
    ratio = b_col_step / t_col_step
    b_row_step = round(ratio * t_row_step)
    
    b_row_starts = sorted(set(b[0] for b in blocks))
    input_row = b_row_starts[0]
    
    # Get block colors in column order
    block_color_seq = [c for _, c in sorted((b[1], b[4]) for b in blocks)]
    n_blocks = len(block_color_seq)
    
    # Find which template row and column offset the input blocks match
    matched_tri = None
    col_offset = 0
    for tri in range(num_tr):
        for offset in range(num_tc - n_blocks + 1):
            if all(template.get((tri, offset + i)) == block_color_seq[i]
                   for i in range(n_blocks)):
                matched_tri = tri
                col_offset = offset
                break
        if matched_tri is not None:
            break
    
    if matched_tri is None:
        return g
    
    actual_col_origin = b_col_starts[0] - col_offset * b_col_step
    
    for tri in range(num_tr):
        block_row = input_row + (tri - matched_tri) * b_row_step
        for tci in range(num_tc):
            if (tri, tci) not in template:
                continue
            color = template[(tri, tci)]
            block_col = actual_col_origin + tci * b_col_step
            for dr in range(block_h):
                for dc in range(block_w):
                    nr, nc = block_row + dr, block_col + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        g[nr][nc] = color
    
    return g

if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        task = json.load(f)
    for i, ex in enumerate(task['train']):
        result = solve(ex['input'])
        print(f"Train {i}: {'PASS' if result == ex['output'] else 'FAIL'}")



def _solve(grid: Grid):
    return solve(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_c4d067a0", g_c4d067a0)]


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
            "engine": "s3_g_c4d067a0",
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
        "engine": "s3_g_c4d067a0",
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
    "g_c4d067a0",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
