"""S1 solid-motif carve language game (FoT).

Grammar family owned here:
  solid_motif_carve (canonical: eval task 58f5dbd5)
    S1: majority color is background; filled rectangles (h,w >= 4) are solids.
    S2: for each solid color C, non-solid C cells form a motif mask (bbox).
    S3: motif size must be (solid_h-2) x (solid_w-2); punch motif-present
        cells in the solid interior to background (invert stamp).
    S4: output = crop covering all solids expanded by one bg frame cell.
    C4: licensed only when every training pair replays exact.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_MIN_SOLID = 4


def _majority(grid: Grid) -> int:
    return Counter(cell for row in grid for cell in row).most_common(1)[0][0]


def _components(grid: Grid, bg: int) -> List[Tuple[int, List[Tuple[int, int]], int, int, int, int]]:
    height, width = len(grid), len(grid[0])
    seen = [[False] * width for _ in range(height)]
    comps: List[Tuple[int, List[Tuple[int, int]], int, int, int, int]] = []
    for r in range(height):
        for c in range(width):
            if seen[r][c] or grid[r][c] == bg:
                continue
            color = grid[r][c]
            queue = deque([(r, c)])
            seen[r][c] = True
            cells: List[Tuple[int, int]] = []
            while queue:
                y, x = queue.popleft()
                cells.append((y, x))
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if (
                        0 <= ny < height
                        and 0 <= nx < width
                        and not seen[ny][nx]
                        and grid[ny][nx] == color
                    ):
                        seen[ny][nx] = True
                        queue.append((ny, nx))
            rows = [y for y, _ in cells]
            cols = [x for _, x in cells]
            comps.append((color, cells, min(rows), max(rows), min(cols), max(cols)))
    return comps


def solid_motif_carve(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    height, width = len(grid), len(grid[0])
    bg = _majority(grid)
    comps = _components(grid, bg)
    solids: List[Tuple[int, int, int, int, int]] = []
    solid_cells: set[Tuple[int, int]] = set()
    for color, cells, r0, r1, c0, c1 in comps:
        h, w = r1 - r0 + 1, c1 - c0 + 1
        if h < _MIN_SOLID or w < _MIN_SOLID:
            continue
        if len(cells) != h * w:
            continue
        solids.append((color, r0, r1, c0, c1))
        solid_cells.update(cells)
    if not solids:
        return None
    solid_colors = {color for color, *_ in solids}
    motifs: Dict[int, List[List[bool]]] = {}
    for color in solid_colors:
        cells = [
            (r, c)
            for r in range(height)
            for c in range(width)
            if grid[r][c] == color and (r, c) not in solid_cells
        ]
        if not cells:
            return None
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        mr0, mr1, mc0, mc1 = min(rows), max(rows), min(cols), max(cols)
        mh, mw = mr1 - mr0 + 1, mc1 - mc0 + 1
        mask = [[False] * mw for _ in range(mh)]
        for r, c in cells:
            mask[r - mr0][c - mc0] = True
        motifs[color] = mask
    for color, r0, r1, c0, c1 in solids:
        mask = motifs[color]
        mh, mw = len(mask), len(mask[0])
        if mh != (r1 - r0 + 1) - 2 or mw != (c1 - c0 + 1) - 2:
            return None
    crop_r0 = min(r0 for _, r0, _, _, _ in solids) - 1
    crop_r1 = max(r1 for _, _, r1, _, _ in solids) + 1
    crop_c0 = min(c0 for _, _, _, c0, _ in solids) - 1
    crop_c1 = max(c1 for _, _, _, _, c1 in solids) + 1
    if crop_r0 < 0 or crop_c0 < 0 or crop_r1 >= height or crop_c1 >= width:
        return None
    out = [list(row[crop_c0 : crop_c1 + 1]) for row in grid[crop_r0 : crop_r1 + 1]]
    for color, r0, r1, c0, c1 in solids:
        mask = motifs[color]
        for i, row in enumerate(mask):
            for j, hit in enumerate(row):
                if hit:
                    out[r0 + 1 - crop_r0 + i][c0 + 1 - crop_c0 + j] = bg
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("solid_motif_carve", solid_motif_carve)]


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
            "engine": "s1_solid_motif_carve",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_solid_motif_carve",
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
    "solid_motif_carve",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
