"""S1 laser-mirror diagonal beams pack (FoT).

Grammar family owned here:
  laser_mirror_beams (canonical: eval task 142ca369)
    S1: L-trominoes (2x2 minus one corner) are laser guns; every other
        non-zero component cell is a mirror.
    S2: each gun emits from the elbow (corner opposite the missing cell)
        along the diagonal pointing away from the missing cell.
    S3: beam steps diagonally, painting empty cells with the current color.
    S4: when a beam cell is 4-adjacent to a mirror, flip the velocity
        component along that axis and recolor to the mirror's color
        (including the reflection cell). Stop at solids / borders.
    C4: train-replay gated; beams of different colors do not need collision
        rules beyond solid occupancy (crossing paths overwrite by emission order).

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]


def _components(grid: Grid) -> List[Tuple[int, List[Cell]]]:
    height = len(grid)
    width = len(grid[0])
    seen = [[False] * width for _ in range(height)]
    comps: List[Tuple[int, List[Cell]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or seen[row][col]:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen[row][col] = True
            cells: List[Cell] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def _l_tromino(cells: Sequence[Cell]) -> Optional[Tuple[Cell, Cell]]:
    if len(cells) != 3:
        return None
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    if r1 - r0 != 1 or c1 - c0 != 1:
        return None
    cellset = set(cells)
    missing = next(
        (r, c) for r in (r0, r1) for c in (c0, c1) if (r, c) not in cellset
    )
    elbow = (r0 + r1 - missing[0], c0 + c1 - missing[1])
    return missing, elbow


def laser_mirror_beams(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    height = len(grid)
    width = len(grid[0])
    comps = _components(grid)
    if not comps:
        return None
    solid: Dict[Cell, int] = {}
    for color, cells in comps:
        for cell in cells:
            solid[cell] = color
    mirrors: Set[Cell] = set()
    guns: List[Tuple[int, int, int, int, int]] = []
    for color, cells in comps:
        tromino = _l_tromino(cells)
        if tromino is None:
            mirrors.update(cells)
            continue
        missing, elbow = tromino
        dr = 1 if elbow[0] > missing[0] else -1
        dc = 1 if elbow[1] > missing[1] else -1
        guns.append((elbow[0], elbow[1], dr, dc, color))
    if not guns:
        return None

    out = [list(row) for row in grid]

    def mirror_neighbor(r: int, c: int) -> Optional[Tuple[int, int]]:
        for mr, mc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if (r + mr, c + mc) in mirrors:
                return mr, mc
        return None

    for r0, c0, dr, dc, color in guns:
        r, c = r0, c0
        cur = color
        for _ in range(height + width + 5):
            r += dr
            c += dc
            if not (0 <= r < height and 0 <= c < width):
                break
            if (r, c) in solid:
                break
            out[r][c] = cur
            rel = mirror_neighbor(r, c)
            if rel is None:
                continue
            mr, mc = rel
            if mr:
                dr = -dr
            if mc:
                dc = -dc
            cur = solid[(r + mr, c + mc)]
            out[r][c] = cur
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("laser_mirror_beams", laser_mirror_beams)]


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
            "engine": "s1_laser_mirror_beams",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_laser_mirror_beams",
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
    "laser_mirror_beams",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
