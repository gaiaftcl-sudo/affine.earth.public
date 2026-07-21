"""S1 frame-chamber staircase language game (FoT).

Grammar family owned here:
  frame_chamber_staircase (canonical: eval task 89565ca0)
    S1: marker = color with the most 4-connected components (scatter noise).
    S2: each remaining non-bg color is a rectangular frame / cage object.
    S3: chamber count = enclosed open regions inside the object's bbox after
        closing the outer border, treating object cells (+ markers that touch
        the object) as walls, sealing near-full divider rows/cols (thr=0.7),
        and dropping size-1 pocket rooms.
    S4: width W = max chamber count; sort objects by (chambers, color);
        emit row color*chambers + marker*(W-chambers) per object.
    C4: exact projection licensed by full train replay.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_SEAL_THR = 0.7
_MIN_ROOM = 2
_MARKER_MIN_OWN_NBR = 1


def _infer_marker(grid: Grid, bg: int = 0) -> Optional[int]:
    height, width = len(grid), len(grid[0])
    best: Optional[int] = None
    best_score: Tuple[int, int] = (-1, 0)
    for col in range(1, 10):
        present = any(grid[r][c] == col for r in range(height) for c in range(width))
        if not present:
            continue
        vis = [[False] * width for _ in range(height)]
        ncc = 0
        cells = 0
        for r in range(height):
            for c in range(width):
                if grid[r][c] != col or vis[r][c]:
                    continue
                ncc += 1
                stack = [(r, c)]
                vis[r][c] = True
                while stack:
                    y, x = stack.pop()
                    cells += 1
                    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                        ny, nx = y + dy, x + dx
                        if (
                            0 <= ny < height
                            and 0 <= nx < width
                            and not vis[ny][nx]
                            and grid[ny][nx] == col
                        ):
                            vis[ny][nx] = True
                            stack.append((ny, nx))
        score = (ncc, -cells)
        if score > best_score:
            best_score = score
            best = col
    return best


def _chamber_count(grid: Grid, col: int, marker: int) -> int:
    height, width = len(grid), len(grid[0])
    own = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == col
    ]
    if not own:
        return 0
    r0 = min(r for r, _ in own)
    r1 = max(r for r, _ in own)
    c0 = min(c for _, c in own)
    c1 = max(c for _, c in own)
    if r1 - r0 < 2 or c1 - c0 < 2:
        return 1

    walls = set()
    for c in range(c0, c1 + 1):
        walls.add((r0, c))
        walls.add((r1, c))
    for r in range(r0, r1 + 1):
        walls.add((r, c0))
        walls.add((r, c1))
    for p in own:
        walls.add(p)

    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if grid[r][c] != marker:
                continue
            n_own = sum(
                1
                for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0))
                if 0 <= r + dy < height
                and 0 <= c + dx < width
                and grid[r + dy][c + dx] == col
            )
            if n_own >= _MARKER_MIN_OWN_NBR:
                walls.add((r, c))

    h_int = r1 - r0 - 1
    w_int = c1 - c0 - 1
    if h_int > 0 and w_int > 0:
        for r in range(r0 + 1, r1):
            hits = sum(
                1
                for c in range(c0 + 1, c1)
                if (r, c) in walls or grid[r][c] in (col, marker)
            )
            if hits / w_int >= _SEAL_THR:
                for c in range(c0, c1 + 1):
                    walls.add((r, c))
        for c in range(c0 + 1, c1):
            hits = sum(
                1
                for r in range(r0 + 1, r1)
                if (r, c) in walls or grid[r][c] in (col, marker)
            )
            if hits / h_int >= _SEAL_THR:
                for r in range(r0, r1 + 1):
                    walls.add((r, c))

    vis = set()
    sizes: List[int] = []
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            if (r, c) in walls or (r, c) in vis:
                continue
            stack = [(r, c)]
            vis.add((r, c))
            size = 0
            while stack:
                y, x = stack.pop()
                size += 1
                for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    ny, nx = y + dy, x + dx
                    if (
                        r0 < ny < r1
                        and c0 < nx < c1
                        and (ny, nx) not in walls
                        and (ny, nx) not in vis
                    ):
                        vis.add((ny, nx))
                        stack.append((ny, nx))
            sizes.append(size)
    sizes = [s for s in sizes if s >= _MIN_ROOM]
    return max(len(sizes), 1)


def frame_chamber_staircase(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    marker = _infer_marker(grid)
    if marker is None:
        return None
    colors = sorted(
        {
            cell
            for row in grid
            for cell in row
            if cell not in (0, marker)
        }
    )
    if not colors:
        return None
    scored: List[Tuple[int, int]] = []
    for col in colors:
        chambers = _chamber_count(grid, col, marker)
        if chambers <= 0:
            return None
        scored.append((chambers, col))
    scored.sort()
    width = max(chambers for chambers, _ in scored)
    if width <= 0:
        return None
    out: Grid = []
    for chambers, col in scored:
        pad = width - chambers
        if pad < 0:
            return None
        out.append([col] * chambers + [marker] * pad)
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("frame_chamber_staircase", frame_chamber_staircase)]


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
            "engine": "s1_frame_chamber_staircase",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_frame_chamber_staircase",
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
    "frame_chamber_staircase",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
