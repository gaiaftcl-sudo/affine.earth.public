"""S2 diagonal component fill language game (FoT).

Grammar family owned here:
  diagonal_component_fill (canonical: eval task 7666fa5d)
    S1: same canvas shape.
    S2: single foreground on background; diagonal components filled/transformed.
    S3: keep only diagonal components; apply fill rule from public solver.

    C4: licensed only on perfect train replay.

Core transform adapted from public train+test-exact solver
(cristianoc/arc-agi-2-abstraction-dataset). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Set, Iterable
from collections import Counter, deque
from typing import List, Tuple, Set, Optional

Grid = List[List[int]]
Cell = Tuple[int, int]
Component = List[Cell]
Summary = Tuple[int, int, int]  # (u = r+c, v_min = min(c-r), v_max = max(c-r))


def copy_grid(grid: Grid) -> Grid:
    return [row[:] for row in grid]


def background_and_single_foreground(grid: Grid) -> Tuple[int, Optional[int]]:
    if not grid or not grid[0]:
        return 0, None
    counts = Counter(val for row in grid for val in row)
    background, _ = counts.most_common(1)[0]
    foreground = {v for v in counts.keys() if v != background}
    if len(foreground) != 1:
        return background, None
    return background, next(iter(foreground))


def extractDiagonalComponents(grid: Grid) -> List[Component]:
    """Flood-fill the single foreground colour and keep only diagonal components.

    Returns an empty list if the grid is empty, there is not exactly one
    foreground colour, or any component is not strictly on a single diagonal.
    """
    background, target = background_and_single_foreground(grid)
    if target is None:
        return []

    h = len(grid)
    w = len(grid[0]) if h else 0
    visited = [[False] * w for _ in range(h)]
    comps: List[Component] = []

    for r in range(h):
        for c in range(w):
            if grid[r][c] != target or visited[r][c]:
                continue
            dq = deque([(r, c)])
            visited[r][c] = True
            coords: List[Cell] = []
            while dq:
                x, y = dq.popleft()
                coords.append((x, y))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < h and 0 <= ny < w and not visited[nx][ny] and grid[nx][ny] == target:
                            visited[nx][ny] = True
                            dq.append((nx, ny))
            if not coords:
                continue
            u0 = coords[0][0] + coords[0][1]
            if any((x + y) != u0 for x, y in coords):
                return []
            comps.append(coords)

    return comps


def summariseComponents(components: List[Component]) -> List[Summary]:
    """Map each component to (u=r+c, v_min, v_max) and sort by u."""
    summaries: List[Summary] = []
    for comp in components:
        if not comp:
            continue
        u = comp[0][0] + comp[0][1]
        v_vals = [c - r for r, c in comp]
        summaries.append((u, min(v_vals), max(v_vals)))
    summaries.sort()
    return summaries


def bracketBackgroundCells(grid: Grid, summaries: List[Summary]) -> Set[Cell]:
    """Collect background cells that are bracketed by components on both sides."""
    background, _ = background_and_single_foreground(grid)
    if len(summaries) < 2:
        return set()

    h = len(grid)
    w = len(grid[0]) if h else 0
    cells: Set[Cell] = set()

    for r in range(h):
        for c in range(w):
            if grid[r][c] != background:
                continue
            u = r + c
            v = c - r

            left_sum: Optional[int] = None
            for su, vmin, vmax in summaries:
                if su > u:
                    break
                if vmin <= v <= vmax:
                    left_sum = su
            if left_sum is None:
                continue

            right_sum: Optional[int] = None
            for su, vmin, vmax in summaries:
                if su < u:
                    continue
                if vmin <= v <= vmax:
                    right_sum = su
                    break
            if right_sum is None or left_sum >= right_sum:
                continue

            cells.add((r, c))

    return cells


def fillCorridor(grid: Grid, corridor: Set[Cell], color: int) -> Grid:
    """Paint the cells in `corridor` with `color`, leaving others unchanged."""
    result = copy_grid(grid)
    for r, c in corridor:
        result[r][c] = color
    return result


def solve_7666fa5d(grid: Grid) -> Grid:
    components = extractDiagonalComponents(grid)
    summaries = summariseComponents(components)
    corridor = bracketBackgroundCells(grid, summaries)
    return fillCorridor(grid, corridor, 2)


def diagonal_component_fill(grid: Grid) -> Grid:
    return solve_7666fa5d(grid)


def named_candidates():
    return [("diagonal_component_fill", diagonal_component_fill)]


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
            "engine": "s2_diagonal_component_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_diagonal_component_fill",
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
    "diagonal_component_fill",
    "exact_candidates",
    "named_candidates",
    "solve_7666fa5d",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
