"""S2 tagged-shape border pack language game (FoT).

Grammar family owned here:
  tagged_shape_border_pack (canonical: eval task 446ef5d2)
    S1: same canvas; majority = background.
    S2: 8-connected components; unique minority tag color marks orientation.
    S3: remaining shapes pack into a border-colored rectangle.
    S4: place packed rect near tag corner (top/bottom × left/right) with margin 2.
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 446ef5d2). Never submits to Kaggle.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def tagged_shape_border_pack(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    if len(out) != len(grid) or len(out[0]) != len(grid[0]):
        return None
    return out


def _solve(grid):
    H, W = len(grid), len(grid[0])

    # Detect background color as most common value
    counts = Counter()
    for row in grid:
        for v in row:
            counts[v] += 1
    bg = counts.most_common(1)[0][0]

    visited = [[False]*W for _ in range(H)]
    components = []
    for r in range(H):
        for c in range(W):
            if not visited[r][c] and grid[r][c] != bg:
                q = deque([(r,c)]); visited[r][c] = True; cells = {}
                while q:
                    cr, cc = q.popleft(); cells[(cr,cc)] = grid[cr][cc]
                    for dr in [-1,0,1]:
                        for dc in [-1,0,1]:
                            if dr==0 and dc==0: continue
                            nr, nc = cr+dr, cc+dc
                            if 0<=nr<H and 0<=nc<W and not visited[nr][nc] and grid[nr][nc] != bg:
                                visited[nr][nc] = True; q.append((nr,nc))
                components.append(cells)

    color_comp = {}
    for ci, cells in enumerate(components):
        for v in set(cells.values()):
            color_comp.setdefault(v, set()).add(ci)

    tag_color = None
    tag_comp_idx = None
    for color, comps in color_comp.items():
        if len(comps) == 1:
            ci = list(comps)[0]
            comp_cells = components[ci]
            tag_cells = sum(1 for v in comp_cells.values() if v == color)
            non_tag = sum(1 for v in comp_cells.values() if v != color)
            if tag_cells < non_tag:
                tag_color = color; tag_comp_idx = ci; break

    edge_counts = Counter()
    for cells in components:
        for v in cells.values():
            if v != tag_color:
                edge_counts[v] += 1
    border_color = edge_counts.most_common(1)[0][0]

    # Extract shapes as cell-offset lists to handle non-rectangular (L-shaped) pieces
    shapes = []
    tag_direction = None
    for ci, cells in enumerate(components):
        clean = {(r,c): v for (r,c), v in cells.items() if v != tag_color}
        if not clean: continue
        min_r = min(r for r,c in clean)
        min_c = min(c for r,c in clean)
        shape = sorted([(r-min_r, c-min_c, v) for (r,c), v in clean.items()])
        shapes.append(shape)

        if ci == tag_comp_idx and tag_color is not None:
            tag_cells_list = [(r,c) for (r,c),v in cells.items() if v == tag_color]
            if tag_cells_list:
                tag_cr = sum(r for r,c in tag_cells_list)/len(tag_cells_list)
                tag_cc = sum(c for r,c in tag_cells_list)/len(tag_cells_list)
                core_cr = sum(r for r,c in clean)/len(clean)
                core_cc = sum(c for r,c in clean)/len(clean)
                vd = 'bottom' if tag_cr > core_cr else 'top'
                hd = 'right' if tag_cc > core_cc else 'left'
                tag_direction = (vd, hd)

    n = len(shapes)
    total_cells = sum(len(s) for s in shapes)
    bc = border_color

    def try_tile(oh, ow):
        output = [[-1]*ow for _ in range(oh)]
        used = [False]*n

        def fill():
            for r in range(oh):
                for c in range(ow):
                    if output[r][c] == -1:
                        for i in range(n):
                            if used[i]: continue
                            shape = shapes[i]
                            ok = True
                            for dr, dc, v in shape:
                                nr, nc = r+dr, c+dc
                                if nr < 0 or nr >= oh or nc < 0 or nc >= ow:
                                    ok = False; break
                                if output[nr][nc] != -1:
                                    ok = False; break
                            if not ok: continue

                            for dr, dc, v in shape:
                                output[r+dr][c+dc] = v
                            used[i] = True

                            if fill(): return True

                            for dr, dc, _ in shape:
                                output[r+dr][c+dc] = -1
                            used[i] = False
                        return False
            # All filled — validate border
            for c2 in range(ow):
                if output[0][c2] != bc or output[oh-1][c2] != bc: return False
            for r2 in range(oh):
                if output[r2][0] != bc or output[r2][ow-1] != bc: return False
            return True

        if fill():
            return [row[:] for row in output]
        return None

    possible_dims = []
    for oh in range(1, total_cells+1):
        if total_cells % oh == 0:
            ow = total_cells // oh
            if oh <= H and ow <= W:
                possible_dims.append((oh, ow))
    possible_dims.sort(key=lambda x: abs(x[0]-x[1]))

    for oh, ow in possible_dims:
        result = try_tile(oh, ow)
        if result is not None:
            out = [[bg]*W for _ in range(H)]
            if tag_direction:
                vd, hd = tag_direction
                sr = 2 if vd == 'top' else H-oh-2
                sc = 2 if hd == 'left' else W-ow-2
            else:
                sr = (H-oh)//2; sc = (W-ow)//2
            for r in range(oh):
                for c in range(ow):
                    out[sr+r][sc+c] = result[r][c]
            return out
    return grid



def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("tagged_shape_border_pack", tagged_shape_border_pack)]


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
            "engine": "s2_tagged_shape_border_pack",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_tagged_shape_border_pack",
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
    "solve_task",
    "submission_fragment",
    "tagged_shape_border_pack",
    "train_replay",
]
