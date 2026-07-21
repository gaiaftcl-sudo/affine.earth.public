"""Batch FoT engine for eval task 5dbc8537.

Grammar family owned here:
  sprite_align_compose (canonical: eval task 5dbc8537)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 5dbc8537). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def sprite_align_compose(grid: Grid) -> Optional[Grid]:
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
Solver for ARC puzzle 5dbc8537

The input grid has two regions separated along one axis:
1. TEMPLATE: A shape defined by a border color with interior holes (bg/hole color)
2. CONTENT: Colored rectangular blocks on a background (same color as the holes)

The output is the template region with its holes filled by the content blocks,
matched by dimensions (height × width). Blocks are placed greedily by area (largest first).
"""
import json
from collections import defaultdict


def _solve(grid: list[list[int]]) -> list[list[int]]:
    R, C = len(grid), len(grid[0])

    # Find the template and content regions by trying all 4 possible splits
    result = None
    for split_type in ["left", "right", "top", "bottom"]:
        res = try_split(grid, R, C, split_type)
        if res is not None:
            result = res
            break

    if result is None:
        raise ValueError("Could not find valid split")
    return result


def try_split(grid, R, C, split_type):
    """Try a specific split orientation and return the solved output or None."""
    # Find where to split by looking for a region with exactly 2 distinct values
    best = None
    for size in range(2, max(R, C)):
        if split_type == "left" and size < C:
            t_cells = [(r, c) for r in range(R) for c in range(size)]
            c_cells = [(r, c) for r in range(R) for c in range(size, C)]
            out_shape = (R, size)
        elif split_type == "right" and size < C:
            t_cells = [(r, c) for r in range(R) for c in range(C - size, C)]
            c_cells = [(r, c) for r in range(R) for c in range(C - size)]
            out_shape = (R, size)
        elif split_type == "top" and size < R:
            t_cells = [(r, c) for r in range(size) for c in range(C)]
            c_cells = [(r, c) for r in range(size, R) for c in range(C)]
            out_shape = (size, C)
        elif split_type == "bottom" and size < R:
            t_cells = [(r, c) for r in range(R - size, R) for c in range(C)]
            c_cells = [(r, c) for r in range(R - size) for c in range(C)]
            out_shape = (size, C)
        else:
            continue

        t_vals = set(grid[r][c] for r, c in t_cells)
        if len(t_vals) == 2:
            c_vals = set(grid[r][c] for r, c in c_cells)
            shared = t_vals & c_vals
            border_only = t_vals - c_vals
            if len(border_only) == 1 and len(shared) >= 1:
                border_color = list(border_only)[0]
                hole_color = list(shared)[0] if len(shared) == 1 else max(
                    shared, key=lambda v: sum(1 for r, c in t_cells if grid[r][c] == v)
                )
                best = (split_type, size, border_color, hole_color, out_shape, t_cells, c_cells)
                break

    if best is None:
        return None

    split_type, size, border_color, hole_color, out_shape, t_cells, c_cells = best
    oR, oC = out_shape

    # Determine template origin in the grid
    if split_type == "left":
        t_r0, t_c0 = 0, 0
    elif split_type == "right":
        t_r0, t_c0 = 0, C - size
    elif split_type == "top":
        t_r0, t_c0 = 0, 0
    elif split_type == "bottom":
        t_r0, t_c0 = R - size, 0

    # Build the output grid (start with template as-is)
    output = []
    for i in range(oR):
        row = []
        for j in range(oC):
            row.append(grid[t_r0 + i][t_c0 + j])
        output.append(row)

    # Find hole positions in the template (relative to output)
    holes = set()
    for i in range(oR):
        for j in range(oC):
            if output[i][j] == hole_color:
                holes.add((i, j))

    # Extract content blocks from content region
    content_cells = set(c_cells)
    blocks = extract_blocks(grid, content_cells, hole_color)

    # Sort blocks by area (largest first) for efficient backtracking
    blocks.sort(key=lambda b: b[0] * b[1], reverse=True)

    # Use backtracking to find the unique valid tiling
    remaining = set(holes)
    placement = [None] * len(blocks)

    def backtrack(idx):
        if idx == len(blocks):
            return len(remaining) == 0
        h, w, pattern = blocks[idx]
        # Find the top-left-most remaining cell to constrain search
        for i in range(oR):
            for j in range(oC):
                if can_place(remaining, i, j, h, w):
                    # Try placing here
                    placed_cells = set()
                    for di in range(h):
                        for dj in range(w):
                            placed_cells.add((i + di, j + dj))
                    remaining.difference_update(placed_cells)
                    placement[idx] = (i, j)
                    if backtrack(idx + 1):
                        return True
                    remaining.update(placed_cells)
                    placement[idx] = None
        return False

    if not backtrack(0):
        # Try without strict "all holes filled" constraint
        # Just place blocks greedily
        remaining = set(holes)
        for idx, (h, w, pattern) in enumerate(blocks):
            for i in range(oR):
                for j in range(oC):
                    if can_place(remaining, i, j, h, w):
                        for di in range(h):
                            for dj in range(w):
                                remaining.discard((i + di, j + dj))
                        placement[idx] = (i, j)
                        break
                if placement[idx] is not None:
                    break

    # Apply placements to output
    for idx, (h, w, pattern) in enumerate(blocks):
        if placement[idx] is not None:
            pi, pj = placement[idx]
            for di in range(h):
                for dj in range(w):
                    output[pi + di][pj + dj] = pattern[di][dj]

    return output


def can_place(remaining, r, c, h, w):
    """Check if a h×w rectangle at (r,c) fits entirely within remaining holes."""
    for di in range(h):
        for dj in range(w):
            if (r + di, c + dj) not in remaining:
                return False
    return True


def extract_blocks(grid, content_cells, bg_color):
    """Extract rectangular blocks from the content region."""
    R = max(r for r, c in content_cells) + 1
    C = max(c for r, c in content_cells) + 1

    # Find non-bg cells
    non_bg = set()
    for r, c in content_cells:
        if grid[r][c] != bg_color:
            non_bg.add((r, c))

    # Find connected components (4-connected)
    visited = set()
    blocks = []

    for start in non_bg:
        if start in visited:
            continue
        # BFS
        component = set()
        queue = [start]
        while queue:
            cell = queue.pop()
            if cell in visited:
                continue
            visited.add(cell)
            component.add(cell)
            r, c = cell
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in non_bg and (nr, nc) not in visited:
                    queue.append((nr, nc))

        # Get bounding box
        min_r = min(r for r, c in component)
        max_r = max(r for r, c in component)
        min_c = min(c for r, c in component)
        max_c = max(c for r, c in component)
        h = max_r - min_r + 1
        w = max_c - min_c + 1

        # Extract pattern
        pattern = []
        for i in range(h):
            row = []
            for j in range(w):
                row.append(grid[min_r + i][min_c + j])
            pattern.append(row)

        blocks.append((h, w, pattern))

    return blocks



def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("sprite_align_compose", sprite_align_compose)]


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
            "engine": "s3_sprite_align_compose",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_sprite_align_compose",
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
    "sprite_align_compose",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
