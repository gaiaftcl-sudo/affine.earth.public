"""Batch FoT engine for eval task 800d221b.

Grammar family owned here:
  bbox_motif_stamp (canonical: eval task 800d221b)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 800d221b). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def bbox_motif_stamp(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


from collections import Counter, deque

def _solve(grid):
    H, W = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    
    # bg = most common, border = second most common
    all_colors = Counter(grid[r][c] for r in range(H) for c in range(W))
    sorted_colors = all_colors.most_common()
    bg = sorted_colors[0][0]
    border = sorted_colors[1][0]
    colored_colors = set(all_colors.keys()) - {bg, border}
    
    # Find junction center: border cell where entire 3x3 is border
    junction_center = None
    for r in range(1, H-1):
        for c in range(1, W-1):
            if grid[r][c] == border and all(
                grid[r+dr][c+dc] == border 
                for dr in [-1,0,1] for dc in [-1,0,1]):
                junction_center = (r, c)
                break
        if junction_center:
            break
    
    # Ring cells = 8 neighbors of center
    ring = set()
    if junction_center:
        jr, jc = junction_center
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr != 0 or dc != 0:
                    ring.add((jr+dr, jc+dc))
    
    # Find colored regions
    visited = [[False]*W for _ in range(H)]
    regions = []
    for r in range(H):
        for c in range(W):
            if not visited[r][c] and grid[r][c] in colored_colors:
                q = deque([(r,c)])
                visited[r][c] = True
                cells = []
                while q:
                    cr, cc = q.popleft()
                    cells.append((cr, cc, grid[cr][cc]))
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = cr+dr, cc+dc
                        if 0<=nr<H and 0<=nc<W and not visited[nr][nc] and grid[nr][nc] in colored_colors:
                            visited[nr][nc] = True
                            q.append((nr, nc))
                regions.append(cells)
    
    region_majorities = []
    for cells in regions:
        counts = Counter(v for _,_,v in cells)
        region_majorities.append(counts.most_common(1)[0][0])
    
    
    # Multi-source BFS from colored regions through border cells
    # Ring cells act as barriers and are excluded from BFS
    dist = [[float('inf')]*W for _ in range(H)]
    color_assign = [[None]*W for _ in range(H)]
    conflict = [[False]*W for _ in range(H)]
    
    blocked = ring | ({junction_center} if junction_center else set())
    
    queue = deque()
    for ri, cells in enumerate(regions):
        maj = region_majorities[ri]
        for r, c, v in cells:
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0<=nr<H and 0<=nc<W and grid[nr][nc] == border and (nr, nc) not in blocked:
                    if dist[nr][nc] > 0:
                        dist[nr][nc] = 0
                        color_assign[nr][nc] = maj
                        queue.append((nr, nc))
                    elif dist[nr][nc] == 0 and color_assign[nr][nc] != maj:
                        conflict[nr][nc] = True
    
    while queue:
        r, c = queue.popleft()
        if conflict[r][c]:
            continue
        cur_color = color_assign[r][c]
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0<=nr<H and 0<=nc<W and grid[nr][nc] == border and (nr, nc) not in blocked:
                new_dist = dist[r][c] + 1
                if new_dist < dist[nr][nc]:
                    dist[nr][nc] = new_dist
                    color_assign[nr][nc] = cur_color
                    queue.append((nr, nc))
                elif new_dist == dist[nr][nc] and color_assign[nr][nc] != cur_color:
                    conflict[nr][nc] = True
    
    # Junction center color = majority of colors assigned to border cells adjacent to ring
    junction_color = None
    if junction_center:
        adj_colors = []
        for rr, rc in ring:
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = rr+dr, rc+dc
                if (nr, nc) not in blocked and 0<=nr<H and 0<=nc<W and color_assign[nr][nc] is not None:
                    adj_colors.append(color_assign[nr][nc])
        if adj_colors:
            junction_color = Counter(adj_colors).most_common(1)[0][0]
    
    # Apply colors to border cells
    for r in range(H):
        for c in range(W):
            if grid[r][c] == border:
                if (r, c) in ring:
                    pass  # Ring stays as border
                elif junction_center and (r, c) == junction_center:
                    if junction_color is not None:
                        output[r][c] = junction_color
                elif not conflict[r][c] and color_assign[r][c] is not None:
                    output[r][c] = color_assign[r][c]
    
    return output



def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("bbox_motif_stamp", bbox_motif_stamp)]


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
            "engine": "s3_bbox_motif_stamp",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_bbox_motif_stamp",
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
    "bbox_motif_stamp",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
