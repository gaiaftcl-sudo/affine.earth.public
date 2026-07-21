"""S1 seven-tab merge language game (FoT).

Grammar family owned here:
  seven_tab_merge (canonical: eval task 20270e3b)
    S1: output canvas size ≠ input (crop to merged bbox).
    S2: color 7 is a registration tab; color 4 is object; color 1 is background.
    S3: either (a) full rows of 7 split panels — keep panels containing 4 and stack;
        or (b) ≥2 {4,7}-components — paste non-tab cells of each source onto the
        largest base so the source cell nearest its 7-tab lands on min(base 7-tab).
    S4: orphans (4-only comps) attach to nearest tabbed component before paste.
    C4: exact merged grid; licensed only when every training pair replays.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cells = Dict[Tuple[int, int], int]

TAB = 7
OBJ = 4
BG = 1


def _components(grid: Grid, colors: Sequence[int]) -> List[Cells]:
    height, width = len(grid), len(grid[0])
    seen = [[False] * width for _ in range(height)]
    color_set = set(colors)
    out: List[Cells] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] not in color_set or seen[row][col]:
                continue
            queue = deque([(row, col)])
            seen[row][col] = True
            cells: Cells = {}
            while queue:
                r, c = queue.popleft()
                cells[(r, c)] = grid[r][c]
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] in color_set
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))
            out.append(cells)
    return out


def _center(cells: Cells) -> Tuple[float, float]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return (min(rows) + max(rows)) / 2, (min(cols) + max(cols)) / 2


def _closest(points: Sequence[Tuple[int, int]], origin: Tuple[int, int]) -> Tuple[int, int]:
    return min(
        points,
        key=lambda p: (abs(p[0] - origin[0]) + abs(p[1] - origin[1]), p),
    )


def _stack_sep_rows(grid: Grid) -> Optional[Grid]:
    height = len(grid)
    is_sep = [all(value == TAB for value in grid[row]) for row in range(height)]
    if not any(is_sep):
        return None
    blocks: List[Grid] = []
    row = 0
    while row < height:
        if is_sep[row]:
            row += 1
            continue
        block: Grid = []
        while row < height and not is_sep[row]:
            block.append(list(grid[row]))
            row += 1
        if block:
            blocks.append(block)
    keep = [block for block in blocks if any(value == OBJ for row in block for value in row)]
    if not keep:
        return None
    out: Grid = []
    for block in keep:
        out.extend(block)
    return out


def seven_tab_merge(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    stacked = _stack_sep_rows(grid)
    if stacked is not None:
        return stacked

    comps = _components(grid, (OBJ, TAB))
    with_tab: List[Cells] = []
    orphans: List[Cells] = []
    for cells in comps:
        if any(value == TAB for value in cells.values()):
            with_tab.append(cells)
        else:
            orphans.append(cells)
    if len(with_tab) < 2:
        return None

    merged = [dict(cells) for cells in with_tab]
    for orphan in orphans:
        oc = _center(orphan)
        best = min(
            range(len(merged)),
            key=lambda i: (_center(merged[i])[0] - oc[0]) ** 2
            + (_center(merged[i])[1] - oc[1]) ** 2,
        )
        merged[best].update(orphan)

    merged.sort(key=lambda cells: -sum(1 for value in cells.values() if value != TAB))
    base = merged[0]
    sources = merged[1:]
    base_tabs = [pos for pos, value in base.items() if value == TAB]
    if not base_tabs:
        return None
    dest = min(base_tabs)
    paint: Cells = {
        pos: (BG if value == TAB else value) for pos, value in base.items()
    }

    for source in sources:
        tabs = [pos for pos, value in source.items() if value == TAB]
        rest = {pos: value for pos, value in source.items() if value != TAB}
        if not rest or not tabs:
            continue
        src_tab = min(tabs)
        anchor = _closest(list(rest.keys()), src_tab)
        dr = dest[0] - anchor[0]
        dc = dest[1] - anchor[1]
        for (r, c), value in rest.items():
            rr, cc = r + dr, c + dc
            prev = paint.get((rr, cc), BG)
            paint[(rr, cc)] = OBJ if (prev == OBJ or value == OBJ) else value

    if not paint:
        return None
    rows = [r for r, _ in paint]
    cols = [c for _, c in paint]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    out = [[BG] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for (r, c), value in paint.items():
        out[r - r0][c - c0] = value
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("seven_tab_merge", seven_tab_merge)]


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
            "engine": "s1_seven_tab_merge",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_seven_tab_merge",
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
    "seven_tab_merge",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
