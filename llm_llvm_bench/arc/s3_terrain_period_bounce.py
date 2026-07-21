"""S3 terrain period-bounce language game (FoT).

Grammar family owned here:
  terrain_period_bounce (canonical: eval task 195c6913)
    S1: same canvas shape (in-place spatial rewrite).
    S2: top-2 colors = terrain (bg of left-edge seeds vs the other object).
    S3: 2×2 uniform minority stamps — top-row L→R = period P; remaining stamp = M.
        Left-edge non-terrain singletons seed paths. Erase all stamps/seeds into
        neighboring terrain, then from each seed face East and paint P on bg;
        on object hit place M and alternate facing East↔North; stop on OOB or
        when the new facing has no bg step.
    S4: object/terrain cells not painted stay as erased terrain.
    C4: exact rewrite; licensed only when every training pair replays.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_DIRS = {"N": (-1, 0), "E": (0, 1)}


def _meta(grid: Grid) -> Optional[Dict[str, Any]]:
    if not grid or not grid[0]:
        return None
    height, width = len(grid), len(grid[0])
    flat = [cell for row in grid for cell in row]
    counts = Counter(flat)
    if len(counts) < 2:
        return None
    dominant = {color for color, _ in counts.most_common(2)}

    raw: List[Tuple[int, int, int]] = []
    for row in range(height - 1):
        for col in range(width - 1):
            block = [
                grid[row][col],
                grid[row][col + 1],
                grid[row + 1][col],
                grid[row + 1][col + 1],
            ]
            if len(set(block)) == 1 and block[0] not in dominant:
                raw.append((row, col, block[0]))

    stamps: List[Tuple[int, int, int]] = []
    used: set[Tuple[int, int]] = set()
    for row, col, color in sorted(raw):
        cells = {(row + dr, col + dc) for dr in range(2) for dc in range(2)}
        if cells & used:
            continue
        stamps.append((row, col, color))
        used |= cells

    if len(stamps) < 2:
        return None
    top_row = min(row for row, _, _ in stamps)
    top = sorted([s for s in stamps if s[0] == top_row], key=lambda s: s[1])
    rest = [s for s in stamps if s[0] != top_row]
    if not top or len(rest) != 1:
        return None

    sings: List[Tuple[int, int, int]] = []
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value not in dominant and (row, col) not in used:
                sings.append((row, col, value))
    if not sings:
        return None

    return {
        "dominant": dominant,
        "top": top,
        "rest": rest,
        "sings": sings,
        "used": used,
    }


def _erase(grid: Grid, meta: Dict[str, Any]) -> Grid:
    height, width = len(grid), len(grid[0])
    dominant = meta["dominant"]
    out = [list(row) for row in grid]

    def fill(row: int, col: int) -> None:
        for nr, nc in (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
            (row - 1, col - 1),
            (row - 1, col + 1),
            (row + 1, col - 1),
            (row + 1, col + 1),
        ):
            if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] in dominant:
                out[row][col] = grid[nr][nc]
                return

    for row, col in meta["used"]:
        fill(row, col)
    for row, col, _ in meta["sings"]:
        fill(row, col)
    return out


def terrain_period_bounce(grid: Grid) -> Optional[Grid]:
    meta = _meta(grid)
    if meta is None:
        return None
    height, width = len(grid), len(grid[0])
    period = [color for _, _, color in meta["top"]]
    marker = meta["rest"][0][2]
    base = _erase(grid, meta)
    pred = [list(row) for row in base]

    seed_r, seed_c, _ = meta["sings"][0]
    bg = base[seed_r][seed_c]
    dominant = meta["dominant"]
    others = [color for color in dominant if color != bg]
    if len(others) != 1:
        return None
    obj = others[0]

    def inb(row: int, col: int) -> bool:
        return 0 <= row < height and 0 <= col < width

    for start_r, start_c, _ in meta["sings"]:
        if base[start_r][start_c] != bg:
            return None
        row, col = start_r, start_c
        facing = "E"
        idx = 0
        pred[row][col] = period[idx % len(period)]
        idx += 1
        for _ in range(height * width * 2):
            dr, dc = _DIRS[facing]
            nr, nc = row + dr, col + dc
            if inb(nr, nc) and base[nr][nc] == bg:
                row, col = nr, nc
                pred[row][col] = period[idx % len(period)]
                idx += 1
                continue
            if not inb(nr, nc):
                break
            if base[nr][nc] == obj:
                pred[nr][nc] = marker
            else:
                break
            facing = "N" if facing == "E" else "E"
            dr, dc = _DIRS[facing]
            nr, nc = row + dr, col + dc
            if not (inb(nr, nc) and base[nr][nc] == bg):
                break
    return pred


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("terrain_period_bounce", terrain_period_bounce)]


def exact_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    matched: List[Tuple[str, Transform]] = []
    for name, transform in named_candidates(train):
        ok = True
        for example in train:
            pred = transform(example["input"])
            if pred != example["output"]:
                ok = False
                break
        if ok:
            matched.append((name, transform))
    return matched


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    train = task.get("train", [])
    exact = exact_candidates(train)
    if not exact:
        return {
            "engine": "s3_terrain_period_bounce",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_terrain_period_bounce",
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
    "solve_task",
    "submission_fragment",
    "terrain_period_bounce",
    "train_replay",
]
