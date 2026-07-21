"""S1 wall-tree nested frames pack (FoT).

Grammar family owned here:
  wall_tree_nested_frames (canonical: eval task 13e47133)
    S1: majority color = room fill background; full-height/width uniform
        non-bg separator = wall tree that partitions rooms.
    S2: each 4-connected non-wall component is a room (may be C-shaped).
    S3: room depth = Chebyshev distance from the 8-neighbor boundary
        (cells touching wall / exterior / out-of-region diagonally count
        as depth 0).
    S4: non-bg seeds at depth d set period[d]; missing depth-0 seed injects
        bg; contiguous period from 0 cycles for deeper rings.
    C4: walls preserved; every room cell colored by period[depth % len];
        train-replay gated.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]


def _majority(grid: Grid) -> int:
    return Counter(value for row in grid for value in row).most_common(1)[0][0]


def _wall_color(grid: Grid, bg: int) -> int:
    height = len(grid)
    width = len(grid[0])
    for col in range(width):
        column = [grid[row][col] for row in range(height)]
        if len(set(column)) == 1 and column[0] != bg:
            return column[0]
    for row in range(height):
        if len(set(grid[row])) == 1 and grid[row][0] != bg:
            return grid[row][0]
    counts = Counter(
        value for row in grid for value in row if value != bg
    )
    return counts.most_common(1)[0][0]


def _regions(grid: Grid, wall: int) -> List[List[Cell]]:
    height = len(grid)
    width = len(grid[0])
    seen = [[False] * width for _ in range(height)]
    regions: List[List[Cell]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == wall or seen[row][col]:
                continue
            queue: deque[Cell] = deque([(row, col)])
            seen[row][col] = True
            cells: List[Cell] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] != wall
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))
            regions.append(cells)
    return regions


def _region_depths(cells: Sequence[Cell], grid: Grid) -> Dict[Cell, int]:
    height = len(grid)
    width = len(grid[0])
    cellset: Set[Cell] = set(cells)
    border: List[Cell] = []
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if not (0 <= nr < height and 0 <= nc < width) or (nr, nc) not in cellset:
                    border.append((r, c))
                    break
            else:
                continue
            break
    dist: Dict[Cell, int] = {cell: 10**9 for cell in cells}
    queue: deque[Cell] = deque()
    for cell in border:
        dist[cell] = 0
        queue.append(cell)
    while queue:
        r, c = queue.popleft()
        depth = dist[(r, c)]
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if (nr, nc) in cellset and dist[(nr, nc)] > depth + 1:
                    dist[(nr, nc)] = depth + 1
                    queue.append((nr, nc))
    return dist


def wall_tree_nested_frames(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    bg = _majority(grid)
    wall = _wall_color(grid, bg)
    if wall == bg:
        return None
    out = [list(row) for row in grid]
    painted = False
    for cells in _regions(grid, wall):
        depths = _region_depths(cells, grid)
        markers: Dict[int, int] = {}
        for r, c in cells:
            value = grid[r][c]
            if value not in (bg, wall):
                markers[depths[(r, c)]] = value
        if not markers:
            continue
        if 0 not in markers:
            markers[0] = bg
        period: List[int] = []
        depth = 0
        while depth in markers:
            period.append(markers[depth])
            depth += 1
        if not period:
            continue
        for r, c in cells:
            out[r][c] = period[depths[(r, c)] % len(period)]
        painted = True
    if not painted:
        return None
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("wall_tree_nested_frames", wall_tree_nested_frames)]


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
            "engine": "s1_wall_tree_nested_frames",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_wall_tree_nested_frames",
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
        attempts.append(
            {"attempt_1": pred, "attempt_2": [list(row) for row in pred]}
        )
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
    "train_replay",
    "wall_tree_nested_frames",
]
