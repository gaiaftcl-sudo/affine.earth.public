"""Batch FoT engine for eval task e3721c99.

Grammar family owned here:
  g_e3721c99 (canonical: eval task e3721c99)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · e3721c99). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_e3721c99(grid: Grid) -> Optional[Grid]:
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
Solver for ARC-AGI-2 puzzle e3721c99

Pattern: Topological hole counting with template color mapping.

The grid is divided by a separator line of 1s (a full row or full column) into
a template region and a shape region. Templates are colored rectangles with
varying numbers of interior holes. In the shape region, white (color 5)
connected components have their topological holes counted, and are recolored
to match the template with the same hole count. Components with no matching
template are erased (set to 0).

Algorithm:
1. Find separator (full row or full column of 1s)
2. Find templates on the template side, count their holes, build hole->color map
3. Find connected components of white (5) cells in the shape region
4. Count topological holes in each component (enclosed black regions)
5. Recolor each component based on hole count, or erase if no template matches
"""

import numpy as np
from collections import deque


def solve(input_grid):
    grid = np.array(input_grid, dtype=int)
    H, W = grid.shape
    output = grid.copy()

    # 1. Find separator (full row or full column of 1s)
    sep_row = None
    sep_col = None
    for r in range(H):
        if all(grid[r, c] == 1 for c in range(W)):
            sep_row = r
            break
    if sep_row is None:
        for c in range(W):
            if all(grid[r, c] == 1 for r in range(H)):
                sep_col = c
                break

    # 2. Extract templates and build hole_to_color map
    hole_to_color = {}

    if sep_row is not None:
        # Horizontal separator — templates are above
        templates = _find_templates(grid, range(0, sep_row), range(W))
        for color, cells in templates.items():
            hole_to_color[_count_holes(cells)] = color

    elif sep_col is not None:
        # Vertical separator — template side has no 5s
        left_5s = sum(
            1 for r in range(H) for c in range(sep_col) if grid[r, c] == 5
        )
        right_5s = sum(
            1 for r in range(H) for c in range(sep_col + 1, W) if grid[r, c] == 5
        )
        if left_5s <= right_5s:
            templates = _find_templates(grid, range(H), range(0, sep_col))
        else:
            templates = _find_templates(grid, range(H), range(sep_col + 1, W))
        for color, cells in templates.items():
            hole_to_color[_count_holes(cells)] = color

    else:
        # Fallback: scan first rows for 3-row-tall horizontal templates
        hole_to_color = _scan_horizontal_templates(grid)

    # 3. Find connected components of color 5, count holes, recolor
    visited = np.zeros((H, W), dtype=bool)

    for r in range(H):
        for c in range(W):
            if grid[r, c] == 5 and not visited[r, c]:
                comp = []
                q = deque([(r, c)])
                visited[r, c] = True
                while q:
                    cr, cc = q.popleft()
                    comp.append((cr, cc))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = cr + dr, cc + dc
                        if (
                            0 <= nr < H
                            and 0 <= nc < W
                            and not visited[nr, nc]
                            and grid[nr, nc] == 5
                        ):
                            visited[nr, nc] = True
                            q.append((nr, nc))

                n_holes = _count_holes(comp)
                color = hole_to_color.get(n_holes, 0)
                for pr, pc in comp:
                    output[pr, pc] = color

    return output.tolist()


def _find_templates(grid, row_range, col_range):
    """Find template cells grouped by color in the given region."""
    color_cells: dict[int, list[tuple[int, int]]] = {}
    for r in row_range:
        for c in col_range:
            v = int(grid[r, c])
            if v != 0 and v != 5:
                color_cells.setdefault(v, []).append((r, c))
    return color_cells


def _scan_horizontal_templates(grid):
    """Fallback: scan first rows for 3-row-tall horizontal templates."""
    H, W = grid.shape
    hole_to_color: dict[int, int] = {}

    template_row = None
    for r in range(min(10, H)):
        c = 0
        while c < W:
            v = int(grid[r, c])
            if v not in (0, 5):
                cs = c
                while c < W and int(grid[r, c]) == v:
                    c += 1
                if c - cs >= 3:
                    template_row = r
                    break
            else:
                c += 1
        if template_row is not None:
            break

    if template_row is not None:
        r = template_row
        c = 0
        while c < W:
            v = int(grid[r, c])
            if v not in (0, 5):
                cs = c
                while c < W and int(grid[r, c]) == v:
                    c += 1
                width = c - cs
                if width >= 3 and r + 2 < H:
                    bottom_ok = all(
                        int(grid[r + 2, cc]) == v for cc in range(cs, cs + width)
                    )
                    if bottom_ok:
                        holes = sum(
                            1
                            for dr in range(3)
                            for cc in range(cs, cs + width)
                            if int(grid[r + dr, cc]) == 0
                        )
                        hole_to_color[holes] = v
            else:
                c += 1

    return hole_to_color


def _count_holes(component):
    """Count topological holes in a connected component."""
    comp_set = set(component)
    mnr = min(p[0] for p in comp_set)
    mxr = max(p[0] for p in comp_set)
    mnc = min(p[1] for p in comp_set)
    mxc = max(p[1] for p in comp_set)

    pad = 1
    sh = mxr - mnr + 1 + 2 * pad
    sw = mxc - mnc + 1 + 2 * pad

    ic = set((pr - mnr + pad, pc - mnc + pad) for pr, pc in comp_set)

    # Flood fill external region from corner of padded bounding box
    ext = set()
    fq = deque([(0, 0)])
    ext.add((0, 0))
    while fq:
        fr, fc = fq.popleft()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = fr + dr, fc + dc
            if (
                0 <= nr < sh
                and 0 <= nc < sw
                and (nr, nc) not in ext
                and (nr, nc) not in ic
            ):
                ext.add((nr, nc))
                fq.append((nr, nc))

    # Count connected components of unreachable non-component cells (holes)
    n_holes = 0
    hv = set()
    for pr in range(sh):
        for pc in range(sw):
            if (pr, pc) not in ic and (pr, pc) not in ext and (pr, pc) not in hv:
                n_holes += 1
                hq = deque([(pr, pc)])
                hv.add((pr, pc))
                while hq:
                    hr, hc = hq.popleft()
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = hr + dr, hc + dc
                        if (
                            0 <= nr < sh
                            and 0 <= nc < sw
                            and (nr, nc) not in ic
                            and (nr, nc) not in ext
                            and (nr, nc) not in hv
                        ):
                            hv.add((nr, nc))
                            hq.append((nr, nc))

    return n_holes



def _solve(grid: Grid):
    return solve(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_e3721c99", g_e3721c99)]


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
            "engine": "s3_g_e3721c99",
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
        "engine": "s3_g_e3721c99",
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
    "g_e3721c99",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
