"""Batch FoT engine for eval task 6ffbe589.

Grammar family owned here:
  local_palette_rewrite (canonical: eval task 6ffbe589)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 6ffbe589). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def local_palette_rewrite(grid: Grid) -> Optional[Grid]:
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
Solver for ARC-AGI task 6ffbe589.

Rule: The grid contains a multi-layered pattern and isolated "hint" pixels.
Each color layer in the pattern is independently rotated by (hint_count × 90°) CW,
where hint_count is the number of hint pixels of that color found outside the pattern.
"""

from collections import deque


def _solve(grid: list[list[int]]) -> list[list[int]]:
    rows, cols = len(grid), len(grid[0])

    # Find 8-connected components of non-zero cells
    visited = [[False] * cols for _ in range(rows)]
    components: list[list[tuple[int, int]]] = []
    for sr in range(rows):
        for sc in range(cols):
            if grid[sr][sc] != 0 and not visited[sr][sc]:
                q = deque([(sr, sc)])
                visited[sr][sc] = True
                cells = [(sr, sc)]
                while q:
                    r, c = q.popleft()
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc] and grid[nr][nc] != 0:
                                visited[nr][nc] = True
                                q.append((nr, nc))
                                cells.append((nr, nc))
                components.append(cells)

    # Find the pattern region: start from the largest component's bbox,
    # expand by a margin, and include all non-zero cells within that region.
    # Hint pixels are always far from the main pattern, so they stay outside.
    MARGIN = 3
    components.sort(key=lambda c: -len(c))
    main_comp = components[0]
    pr1 = min(r for r, c in main_comp)
    pr2 = max(r for r, c in main_comp)
    pc1 = min(c for r, c in main_comp)
    pc2 = max(c for r, c in main_comp)

    er1 = max(0, pr1 - MARGIN)
    er2 = min(rows - 1, pr2 + MARGIN)
    ec1 = max(0, pc1 - MARGIN)
    ec2 = min(cols - 1, pc2 + MARGIN)

    # Collect non-zero cells in the expanded region
    pattern_cells: set[tuple[int, int]] = set()
    for r in range(er1, er2 + 1):
        for c in range(ec1, ec2 + 1):
            if grid[r][c] != 0:
                pattern_cells.add((r, c))

    # Pattern bounding box (tight fit around discovered cells)
    min_r = min(r for r, c in pattern_cells)
    max_r = max(r for r, c in pattern_cells)
    min_c = min(c for r, c in pattern_cells)
    max_c = max(c for r, c in pattern_cells)
    R = max_r - min_r + 1
    C = max_c - min_c + 1

    # Extract the pattern
    pattern = [[grid[min_r + r][min_c + c] for c in range(C)] for r in range(R)]

    # Count hint pixels per color (non-zero cells outside the bounding box)
    hints: dict[int, int] = {}
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != 0 and (r < min_r or r > max_r or c < min_c or c > max_c):
                color = grid[r][c]
                hints[color] = hints.get(color, 0) + 1

    # Collect positions per color
    color_positions: dict[int, list[tuple[int, int]]] = {}
    for r in range(R):
        for c in range(C):
            if pattern[r][c] != 0:
                color_positions.setdefault(pattern[r][c], []).append((r, c))

    # Rotate each layer and assemble the result
    result = [[0] * C for _ in range(R)]
    for color, positions in color_positions.items():
        rot_count = hints.get(color, 0) % 4
        rotated = positions
        for _ in range(rot_count):
            rotated = [(c, R - 1 - r) for r, c in rotated]
        for r, c in rotated:
            result[r][c] = color

    return result



def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("local_palette_rewrite", local_palette_rewrite)]


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
            "engine": "s2_local_palette_rewrite",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_local_palette_rewrite",
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
    "local_palette_rewrite",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
