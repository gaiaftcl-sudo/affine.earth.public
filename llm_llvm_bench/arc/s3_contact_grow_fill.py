"""S3 contact grow fill language game (FoT).

Grammar family owned here:
  contact_grow_fill (canonical: eval task db695cfb)
    S3 contact-grow fill from public solver.
    C4: licensed only on perfect train replay.

Core transform adapted from public train+test-exact solver
(cristianoc/arc-agi-2-abstraction-dataset). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from collections import defaultdict
from typing import Dict, List, Tuple, Set, Iterable

Grid = List[List[int]]
Coord = Tuple[int, int]
DiagonalGroups = Dict[str, Dict[int, List[Coord]]]
SixSeeds = Dict[str, Set[Coord]]


def _clone(grid: Grid) -> Grid:
    return [row[:] for row in grid]


def _fill_nwse_path(grid: Grid, output: Grid, coords: List[Coord], six_seeds: SixSeeds) -> None:
    """Fill the NW–SE diagonal segment defined by coords with color 1, collect 6 seeds for anti-diagonal extension."""
    key = coords[0][0] - coords[0][1]  # r - c stays constant on NW–SE diagonals
    rows = [r for r, _ in coords]
    r_min, r_max = min(rows), max(rows)
    width = len(grid[0])
    for r in range(r_min, r_max + 1):
        c = r - key
        if not (0 <= c < width):
            continue
        if grid[r][c] != 6:
            output[r][c] = 1
        if grid[r][c] == 6:
            six_seeds["anti"].add((r, c))  # need NE–SW fill through this seed


def _fill_nesw_path(grid: Grid, output: Grid, coords: List[Coord], six_seeds: SixSeeds) -> None:
    """Fill the NE–SW diagonal segment defined by coords with color 1, collect 6 seeds for main-diagonal extension."""
    key = coords[0][0] + coords[0][1]  # r + c stays constant on NE–SW diagonals
    rows = [r for r, _ in coords]
    r_min, r_max = min(rows), max(rows)
    width = len(grid[0])
    for r in range(r_min, r_max + 1):
        c = key - r
        if not (0 <= c < width):
            continue
        if grid[r][c] != 6:
            output[r][c] = 1
        if grid[r][c] == 6:
            six_seeds["main"].add((r, c))  # need NW–SE fill through this seed


def _fill_diag(output: Grid, seed: Coord, orientation: str) -> None:
    """Paint color 6 along a full diagonal passing through the seed, without overwriting 1-paths."""
    height, width = len(output), len(output[0])
    r0, c0 = seed
    if orientation == "anti":  # NE–SW diagonal (constant r + c)
        diag_sum = r0 + c0
        for r in range(height):
            c = diag_sum - r
            if 0 <= c < width:
                if output[r][c] == 1 and (r, c) != seed:
                    continue
                output[r][c] = 6
    else:  # 'main' -> NW–SE diagonal (constant r - c)
        diff = r0 - c0
        for r in range(height):
            c = r - diff
            if 0 <= c < width:
                if output[r][c] == 1 and (r, c) != seed:
                    continue
                output[r][c] = 6


def groupAnchorsByDiagonal(grid: Grid) -> DiagonalGroups:
    """Group colour-1 anchors by both diagonal orientations (main: NW–SE, anti: NE–SW)."""
    height = len(grid)
    width = len(grid[0]) if grid else 0
    if height == 0 or width == 0:
        return {"main": {}, "anti": {}}

    ones: List[Coord] = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 1]
    groups_main: Dict[int, List[Coord]] = defaultdict(list)
    groups_anti: Dict[int, List[Coord]] = defaultdict(list)
    for r, c in ones:
        groups_main[r - c].append((r, c))
        groups_anti[r + c].append((r, c))
    return {"main": dict(groups_main), "anti": dict(groups_anti)}


def paintOnePaths(grid: Grid, diagonal_groups: DiagonalGroups) -> Tuple[Grid, SixSeeds]:
    """Paint connecting 1-paths for diagonals with at least two anchors; collect perpendicular 6-seeds."""
    painted = _clone(grid)
    six_seeds: SixSeeds = {"anti": set(), "main": set()}

    for coords in diagonal_groups.get("main", {}).values():
        if len(coords) >= 2:
            _fill_nwse_path(grid, painted, coords, six_seeds)

    for coords in diagonal_groups.get("anti", {}).values():
        if len(coords) >= 2:
            _fill_nesw_path(grid, painted, coords, six_seeds)

    return painted, six_seeds


def extendSixDiagonals(painted: Grid, six_seeds: SixSeeds) -> Grid:
    """Extend colour-6 along full diagonals through each recorded seed, preserving 1-paths."""
    extended = _clone(painted)
    for seed in six_seeds.get("anti", set()):
        _fill_diag(extended, seed, "anti")
    for seed in six_seeds.get("main", set()):
        _fill_diag(extended, seed, "main")
    return extended


def finaliseGrid(original: Grid, extended: Grid) -> Grid:
    """Overlay repainted diagonals onto the original grid (already reflected in `extended`)."""
    return extended


def solve_db695cfb(grid: Grid) -> Grid:
    diagonal_groups = groupAnchorsByDiagonal(grid)
    painted, six_seeds = paintOnePaths(grid, diagonal_groups)
    extended = extendSixDiagonals(painted, six_seeds)
    return finaliseGrid(grid, extended)

def contact_grow_fill(grid: Grid) -> Grid:
    return solve_db695cfb(grid)


def named_candidates():
    return [("contact_grow_fill", contact_grow_fill)]


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
            "engine": "s3_contact_grow_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_contact_grow_fill",
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
    "contact_grow_fill",
    "exact_candidates",
    "named_candidates",
    "solve_db695cfb",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
