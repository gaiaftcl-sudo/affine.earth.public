"""S1 ones-stamp period fill language game (FoT).

Grammar family owned here:
  ones_stamp_period_fill (canonical: eval task 53fb4810)
    S1: majority color = background; color-1 components are anchors.
    S2: a contiguous non-bg stamp tile sits on one side of each anchor.
    S3: stamp rows/cols define a period tile; fill is on the opposite side
        of the stamp from the ones (away from the anchor).
    S4: tile the period into bg (and other non-1 cells) along those columns.
    C4: exact fill; licensed only when every training pair replays exact.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _majority(grid: Grid) -> int:
    return Counter(cell for row in grid for cell in row).most_common(1)[0][0]


def _components(grid: Grid, color: int) -> List[List[Tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen = [[False] * width for _ in range(height)]
    comps: List[List[Tuple[int, int]]] = []
    for r in range(height):
        for c in range(width):
            if seen[r][c] or grid[r][c] != color:
                continue
            stack = [(r, c)]
            cells: List[Tuple[int, int]] = []
            seen[r][c] = True
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < height
                        and 0 <= ny < width
                        and not seen[nx][ny]
                        and grid[nx][ny] == color
                    ):
                        seen[nx][ny] = True
                        stack.append((nx, ny))
            comps.append(cells)
    return comps


def ones_stamp_period_fill(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    height, width = len(grid), len(grid[0])
    bg = _majority(grid)
    ones_comps = _components(grid, 1)
    if not ones_comps:
        return None

    out = [list(row) for row in grid]
    painted = False

    def nonempty_cols(r: int) -> List[int]:
        return [c for c in range(width) if grid[r][c] not in (bg, 1)]

    for cells in ones_comps:
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)

        for direction in ("above", "below"):
            if direction == "above":
                if r0 == 0:
                    continue
                adj = r0 - 1
                stamp_cols = [c for c in nonempty_cols(adj) if c0 - 1 <= c <= c1 + 1]
                if not stamp_cols:
                    continue
                stamp_cols = sorted(stamp_cols)
                stamp_rows = [adj]
                r = adj - 1
                while r >= 0 and all(
                    grid[r][c] not in (bg, 1) for c in stamp_cols
                ):
                    stamp_rows.append(r)
                    r -= 1
                stamp_rows = sorted(stamp_rows)
                if not stamp_rows:
                    continue
                period_h = len(stamp_rows)
                tile = [
                    [grid[r][c] for c in stamp_cols] for r in stamp_rows
                ]
                top = stamp_rows[0]
                for r in range(top - 1, -1, -1):
                    idx = (r - stamp_rows[0]) % period_h
                    for j, c in enumerate(stamp_cols):
                        if out[r][c] != 1:
                            out[r][c] = tile[idx][j]
                            painted = True
                break

            if r1 == height - 1:
                continue
            adj = r1 + 1
            stamp_cols = [c for c in nonempty_cols(adj) if c0 - 1 <= c <= c1 + 1]
            if not stamp_cols:
                continue
            stamp_cols = sorted(stamp_cols)
            stamp_rows = [adj]
            r = adj + 1
            while r < height and all(
                grid[r][c] not in (bg, 1) for c in stamp_cols
            ):
                stamp_rows.append(r)
                r += 1
            stamp_rows = sorted(stamp_rows)
            if not stamp_rows:
                continue
            period_h = len(stamp_rows)
            tile = [[grid[r][c] for c in stamp_cols] for r in stamp_rows]
            bottom = stamp_rows[-1]
            for r in range(bottom + 1, height):
                idx = (r - stamp_rows[0]) % period_h
                for j, c in enumerate(stamp_cols):
                    if out[r][c] != 1:
                        out[r][c] = tile[idx][j]
                        painted = True
            break

    if not painted:
        return None
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("ones_stamp_period_fill", ones_stamp_period_fill)]


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
            "engine": "s1_ones_stamp_period_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_ones_stamp_period_fill",
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
    "ones_stamp_period_fill",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
