"""S3 box-slide rail-fill language game (FoT).

Grammar family owned here:
  box_slide_rail_fill (canonical: eval task 271d71e2)
    S1: same canvas shape; background = 6.
    S2: boxes = 0-bordered rectangles whose interiors are {0,5,7}.
    S3: maroon (9) rails flank a slide axis (UP/DOWN/LEFT/RIGHT).
    S4: slide min(rail_gap, n_grey) steps; refill interior by directional
        sweep with n_orange+steps cells as 7 else 5; reattach rails.
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 271d71e2). Never submits to Kaggle.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_BG = 6


def box_slide_rail_fill(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    if len(out) != len(grid) or len(out[0]) != len(grid[0]):
        return None
    return out


def _solve(grid: Grid) -> Grid:
    rows, cols = len(grid), len(grid[0])
    visited: set[Tuple[int, int]] = set()
    boxes: List[Tuple[int, int, int, int]] = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != 0 or (r, c) in visited:
                continue
            queue: deque[Tuple[int, int]] = deque([(r, c)])
            visited.add((r, c))
            cells = [(r, c)]
            while queue:
                cr, cc = queue.popleft()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and (nr, nc) not in visited
                        and grid[nr][nc] in (0, 5, 7)
                    ):
                        visited.add((nr, nc))
                        queue.append((nr, nc))
                        cells.append((nr, nc))
            boxes.append(
                (
                    min(rr for rr, _ in cells),
                    min(cc for _, cc in cells),
                    max(rr for rr, _ in cells),
                    max(cc for _, cc in cells),
                )
            )

    maroon = {(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 9}
    box_info: List[Dict[str, Any]] = []
    for r1, c1, r2, c2 in boxes:
        height, width = r2 - r1 - 1, c2 - c1 - 1
        n_orange = n_grey = 0
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                if grid[r][c] == 7:
                    n_orange += 1
                elif grid[r][c] == 5:
                    n_grey += 1
        side = None
        near_pos = far_pos = distance = 0
        box_width = c2 - c1 + 1
        box_height = r2 - r1 + 1
        if r1 > 0 and sum(
            1 for c in range(c1, c2 + 1) if (r1 - 1, c) in maroon
        ) == box_width:
            side, near_pos = "UP", r1 - 1
            far_pos = near_pos
            for sr in range(near_pos - 1, -1, -1):
                if sum(1 for c in range(c1, c2 + 1) if (sr, c) in maroon) == box_width:
                    far_pos = sr
            distance = near_pos - far_pos
        if side is None and r2 < rows - 1 and sum(
            1 for c in range(c1, c2 + 1) if (r2 + 1, c) in maroon
        ) == box_width:
            side, near_pos = "DOWN", r2 + 1
            far_pos = near_pos
            for sr in range(near_pos + 1, rows):
                if sum(1 for c in range(c1, c2 + 1) if (sr, c) in maroon) == box_width:
                    far_pos = sr
            distance = far_pos - near_pos
        if side is None and c1 > 0 and sum(
            1 for r in range(r1, r2 + 1) if (r, c1 - 1) in maroon
        ) == box_height:
            side, near_pos = "LEFT", c1 - 1
            far_pos = near_pos
            for sc in range(near_pos - 1, -1, -1):
                if sum(1 for r in range(r1, r2 + 1) if (r, sc) in maroon) == box_height:
                    far_pos = sc
            distance = near_pos - far_pos
        if side is None and c2 < cols - 1 and sum(
            1 for r in range(r1, r2 + 1) if (r, c2 + 1) in maroon
        ) == box_height:
            side, near_pos = "RIGHT", c2 + 1
            far_pos = near_pos
            for sc in range(near_pos + 1, cols):
                if sum(1 for r in range(r1, r2 + 1) if (r, sc) in maroon) == box_height:
                    far_pos = sc
            distance = far_pos - near_pos
        movement = min(distance, n_grey) if side else 0
        box_info.append(
            {
                "r1": r1,
                "c1": c1,
                "r2": r2,
                "c2": c2,
                "H": height,
                "W": width,
                "n_orange": n_orange,
                "n_grey": n_grey,
                "side": side,
                "near_pos": near_pos,
                "far_pos": far_pos,
                "distance": distance,
                "movement": movement,
            }
        )

    out = [[_BG] * cols for _ in range(rows)]
    for bi in box_info:
        r1, c1, r2, c2 = bi["r1"], bi["c1"], bi["r2"], bi["c2"]
        height, width, side, movement = bi["H"], bi["W"], bi["side"], bi["movement"]
        dr = dc = 0
        if side == "UP":
            dr = -movement
        elif side == "DOWN":
            dr = movement
        elif side == "LEFT":
            dc = -movement
        elif side == "RIGHT":
            dc = movement
        nr1, nc1, nr2, nc2 = r1 + dr, c1 + dc, r2 + dr, c2 + dc
        for r in range(nr1, nr2 + 1):
            for c in range(nc1, nc2 + 1):
                if r in (nr1, nr2) or c in (nc1, nc2):
                    out[r][c] = 0
        fill_order: List[Tuple[int, int]] = []
        if side == "UP":
            for r in range(height):
                for c in range(width):
                    fill_order.append((r, c))
        elif side == "DOWN":
            for r in range(height - 1, -1, -1):
                for c in range(width - 1, -1, -1):
                    fill_order.append((r, c))
        elif side == "LEFT":
            for c in range(width):
                for r in range(height - 1, -1, -1):
                    fill_order.append((r, c))
        elif side == "RIGHT":
            for c in range(width - 1, -1, -1):
                for r in range(height):
                    fill_order.append((r, c))
        else:
            for r in range(height):
                for c in range(width):
                    fill_order.append((r, c))
        total_orange = bi["n_orange"] + movement
        for idx, (lr, lc) in enumerate(fill_order):
            out[nr1 + 1 + lr][nc1 + 1 + lc] = 7 if idx < total_orange else 5
        near, far = bi["near_pos"], bi["far_pos"]
        if side and movement > 0:
            if side in ("UP", "DOWN"):
                for c in range(nc1, nc2 + 1):
                    out[far][c] = 9
                if movement < bi["distance"]:
                    new_near = near + dr
                    for c in range(nc1, nc2 + 1):
                        out[new_near][c] = 9
            else:
                for r in range(nr1, nr2 + 1):
                    out[r][far] = 9
                if movement < bi["distance"]:
                    new_near = near + dc
                    for r in range(nr1, nr2 + 1):
                        out[r][new_near] = 9
        elif side and movement == 0:
            if side in ("UP", "DOWN"):
                for c in range(c1, c2 + 1):
                    out[near][c] = 9
                    out[far][c] = 9
            else:
                for r in range(r1, r2 + 1):
                    out[r][near] = 9
                    out[r][far] = 9
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("box_slide_rail_fill", box_slide_rail_fill)]


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
            "engine": "s3_box_slide_rail_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_box_slide_rail_fill",
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
    "box_slide_rail_fill",
    "exact_candidates",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
