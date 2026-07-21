"""S2 marker recolor lattice language game (FoT).

Grammar family owned here:
  marker_recolor_lattice (canonical: eval task 8f3a5a89)
    S2 palette rewrite lattice from public solver.
    C4: licensed only on perfect train replay.

Core transform adapted from public train+test-exact solver
(cristianoc/arc-agi-2-abstraction-dataset). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

"""Auto-generated identity stub for ARC-AGI-2 task 8f3a5a89 (split: evaluation).

Refactored to match the DSL-style lambda while preserving behavior.
"""

from collections import deque
from typing import Iterable, List, Set, Tuple

Grid = List[List[int]]
Cell = Tuple[int, int]


def _shape(grid: Grid) -> Tuple[int, int]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    return h, w


def _copy_grid(grid: Grid) -> Grid:
    return [row[:] for row in grid]


def _in_bounds(h: int, w: int, r: int, c: int) -> bool:
    return 0 <= r < h and 0 <= c < w


def floodAccessibleBackground(grid: Grid) -> Set[Cell]:
    """Flood-fill colour-8 cells reachable from the left edge."""
    h, w = _shape(grid)
    if h == 0 or w == 0:
        return set()
    acc: Set[Cell] = set()
    seen = [[False] * w for _ in range(h)]
    q: deque[Cell] = deque()
    for r in range(h):
        if grid[r][0] == 8 and not seen[r][0]:
            seen[r][0] = True
            q.append((r, 0))
    while q:
        r, c = q.popleft()
        acc.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if _in_bounds(h, w, nr, nc) and grid[nr][nc] == 8 and not seen[nr][nc]:
                seen[nr][nc] = True
                q.append((nr, nc))
    return acc


def labelInaccessibleRegions(grid: Grid, accessible: Set[Cell]) -> List[List[bool]]:
    """Label non-accessible components by whether they touch the border.

    Returns a Boolean grid `touch[r][c]` that is True iff the blocked component
    containing (r,c) touches any border. Cells in `accessible` are ignored.
    """
    h, w = _shape(grid)
    touch = [[False] * w for _ in range(h)]
    all_cells = {(r, c) for r in range(h) for c in range(w)}
    blocked = all_cells - accessible
    visited: Set[Cell] = set()
    for cell in blocked:
        if cell in visited:
            continue
        q: deque[Cell] = deque([cell])
        visited.add(cell)
        component: List[Cell] = []
        touches_border = False
        while q:
            r, c = q.popleft()
            component.append((r, c))
            if r in (0, h - 1) or c in (0, w - 1):
                touches_border = True
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if _in_bounds(h, w, nr, nc) and (nr, nc) in blocked and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append((nr, nc))
        for r, c in component:
            touch[r][c] = touches_border
    return touch


def pruneOnes(grid: Grid, accessible: Set[Cell]) -> Grid:
    """Remove colour-1 components that neither touch the left edge nor border the accessible background."""
    h, w = _shape(grid)
    result = _copy_grid(grid)
    seen = [[False] * w for _ in range(h)]
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != 1 or seen[sr][sc]:
                continue
            q: deque[Cell] = deque([(sr, sc)])
            seen[sr][sc] = True
            component: List[Cell] = []
            touches_left = False
            near_access = False
            while q:
                r, c = q.popleft()
                component.append((r, c))
                if c == 0:
                    touches_left = True
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if _in_bounds(h, w, nr, nc) and (nr, nc) in accessible:
                            near_access = True
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if _in_bounds(h, w, nr, nc) and grid[nr][nc] == 1 and not seen[nr][nc]:
                        seen[nr][nc] = True
                        q.append((nr, nc))
            if touches_left or near_access:
                continue
            for r, c in component:
                result[r][c] = 8
    return result


def selectFrontierCells(grid: Grid, accessible: Set[Cell], region_labels: List[List[bool]]) -> Set[Cell]:
    """Choose accessible background cells that neighbour the exterior or diagonal obstacles."""
    h, w = _shape(grid)
    sevens: Set[Cell] = set()

    def neighbor_valid(r: int, c: int) -> bool:
        if not _in_bounds(h, w, r, c):
            return True
        if (r, c) in accessible:
            return False
        return region_labels[r][c]

    for r, c in accessible:
        if any(neighbor_valid(r + dr, c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            sevens.add((r, c))

    for r, c in accessible:
        if (r, c) in sevens:
            continue
        for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            nr, nc = r + dr, c + dc
            if _in_bounds(h, w, nr, nc) and grid[nr][nc] == 1 and region_labels[nr][nc]:
                sevens.add((r, c))
                break

    return sevens


def paintFrontier(grid: Grid, frontier: Set[Cell]) -> Grid:
    """Colour the selected frontier cells with 7 and the remaining accessible background as 8."""
    result = _copy_grid(grid)
    accessible = floodAccessibleBackground(grid)
    for r, c in accessible:
        result[r][c] = 7 if (r, c) in frontier else 8
    return result


def solve_8f3a5a89(grid: Grid) -> Grid:
    accessible = floodAccessibleBackground(grid)
    region_labels = labelInaccessibleRegions(grid, accessible)
    pruned = pruneOnes(grid, accessible)
    frontier = selectFrontierCells(pruned, accessible, region_labels)
    return paintFrontier(pruned, frontier)

def marker_recolor_lattice(grid: Grid) -> Grid:
    return solve_8f3a5a89(grid)


def named_candidates():
    return [("marker_recolor_lattice", marker_recolor_lattice)]


def exact_candidates(train):
    matched = []
    for name, transform in named_candidates():
        try:
            if all(transform(example["input"]) == example["output"] for example in train):
                matched.append((name, transform))
        except Exception:
            continue
    return matched


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    train = task.get("train", [])
    exact = exact_candidates(train)
    if not exact:
        return {
            "engine": "s2_marker_recolor_lattice",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_marker_recolor_lattice",
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
    "marker_recolor_lattice",
    "exact_candidates",
    "named_candidates",
    "solve_8f3a5a89",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
