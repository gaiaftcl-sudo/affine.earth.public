"""S1 dimension-projection language games (FoT).

Grammar family owned here:
  hollow_solid_object_pack (canonical: eval task 2ba387bc)
    S1: output dimensions differ from input (packed object canvas).
    S2: objects partition into hollow frames vs solid fills.
    S3: each partition is sorted by source row, then column-packed.
    S4: left column = hollow, right column = solid (2× object width).
    C4: exact packed rectangular grid licensed by full train replay.

  band_concentric_nest (canonical: eval task 45a5af55)
    S1: output is a larger square; input is full-width uniform row bands.
    S2: bands = maximal runs of identical solid rows (color, thickness).
    S3: outer bands become concentric frames (thickness preserved).
    S4: last band fills the center; size = 2*sum(t[:-1]) + t[-1].
    C4: exact nest licensed by full train replay.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _row_bands(grid: Grid) -> Optional[List[Tuple[int, int]]]:
    """Return [(color, thickness), ...] for full-width uniform row runs."""
    if not grid or not grid[0]:
        return None
    bands: List[Tuple[int, int]] = []
    index = 0
    height = len(grid)
    while index < height:
        row = grid[index]
        if len(set(row)) != 1:
            return None
        color = row[0]
        end = index + 1
        while end < height and grid[end] == row:
            end += 1
        bands.append((color, end - index))
        index = end
    return bands


def band_concentric_nest(grid: Grid) -> Optional[Grid]:
    """Nest horizontal uniform bands as concentric square frames + center fill."""
    bands = _row_bands(grid)
    if bands is None or len(bands) < 2:
        return None
    outer = bands[:-1]
    last_color, last_thickness = bands[-1]
    size = 2 * sum(thickness for _, thickness in outer) + last_thickness
    if size <= 0:
        return None
    out: Grid = [[0] * size for _ in range(size)]
    r0 = c0 = 0
    r1 = c1 = size - 1
    for color, thickness in outer:
        if thickness <= 0 or r0 + thickness - 1 > r1 or c0 + thickness - 1 > c1:
            return None
        for row in range(r0, r0 + thickness):
            for col in range(c0, c1 + 1):
                out[row][col] = color
        for row in range(r1 - thickness + 1, r1 + 1):
            for col in range(c0, c1 + 1):
                out[row][col] = color
        for row in range(r0, r1 + 1):
            for col in range(c0, c0 + thickness):
                out[row][col] = color
            for col in range(c1 - thickness + 1, c1 + 1):
                out[row][col] = color
        r0 += thickness
        r1 -= thickness
        c0 += thickness
        c1 -= thickness
    if r0 > r1 or c0 > c1:
        return None
    if (r1 - r0 + 1) != last_thickness or (c1 - c0 + 1) != last_thickness:
        return None
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            out[row][col] = last_color
    return out


def _background(grid: Grid) -> int:
    counts: Dict[int, int] = {}
    for row in grid:
        for cell in row:
            counts[cell] = counts.get(cell, 0) + 1
    return max(counts.items(), key=lambda item: item[1])[0]


def _components(grid: Grid, bg: int) -> List[List[Tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen = [[False] * width for _ in range(height)]
    comps: List[List[Tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == bg or seen[row][col]:
                continue
            queue = deque([(row, col)])
            seen[row][col] = True
            cells: List[Tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] != bg
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))
            comps.append(cells)
    return comps


def _crop_component(
    grid: Grid, cells: Sequence[Tuple[int, int]], bg: int
) -> Tuple[Tuple[int, int], Grid]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    cellset = set(cells)
    crop = [
        [grid[r][c] if (r, c) in cellset else bg for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]
    return (r0, c0), crop


def _is_hollow(crop: Grid, bg: int) -> bool:
    return any(cell == bg for row in crop for cell in row)


def _pack_two_columns(
    left: Sequence[Grid], right: Sequence[Grid], height: int, width: int, bg: int
) -> Grid:
    rows = max(len(left), len(right))
    out = [[bg] * (2 * width) for _ in range(rows * height)]
    for index, crop in enumerate(left):
        for r in range(height):
            for c in range(width):
                out[index * height + r][c] = crop[r][c]
    for index, crop in enumerate(right):
        for r in range(height):
            for c in range(width):
                out[index * height + r][width + c] = crop[r][c]
    return out


def hollow_solid_object_pack(grid: Grid, bg: Optional[int] = None) -> Optional[Grid]:
    """Pack equal-size objects: hollow frames left, solids right, by source row."""
    if not grid or not grid[0]:
        return None
    if bg is None:
        bg = _background(grid)
    meta = [_crop_component(grid, cells, bg) for cells in _components(grid, bg)]
    if len(meta) < 2:
        return None
    shapes = {(len(crop), len(crop[0])) for _, crop in meta}
    if len(shapes) != 1:
        return None
    height, width = next(iter(shapes))
    hollow = [
        crop
        for origin, crop in sorted(meta, key=lambda item: item[0][0])
        if _is_hollow(crop, bg)
    ]
    solid = [
        crop
        for origin, crop in sorted(meta, key=lambda item: item[0][0])
        if not _is_hollow(crop, bg)
    ]
    if not hollow and not solid:
        return None
    return _pack_two_columns(hollow, solid, height, width, bg)


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    """Return dimension-projection candidates; caller enforces train replay."""
    _ = train  # reserved for train-conditioned variants
    return [
        ("band_concentric_nest", band_concentric_nest),
        ("hollow_solid_object_pack", hollow_solid_object_pack),
    ]


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
            "engine": "s1_dimension_projection",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_dimension_projection",
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
    "band_concentric_nest",
    "exact_candidates",
    "hollow_solid_object_pack",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
