"""Container period-tiling repair for ARC tasks such as 135a2760.

C4 (FoT, train replay 2/2 + labeled eval exact on 135a2760):
  Within each local container, repair anomalous cells so content forms a
  majority-vote periodic tiling:
    - Stacked frame-separated panels → horizontal period along each content row
      (inset past constant wall columns).
    - Color-3 column boxes (≥2 side-by-side) → vertical period over row
      signatures of the column interior.

Prior incomplete C4 ("horizontal reflection of color 1 inside color-3 bbox")
only covers train[0]; train[1] repairs colors {1,3,4,8,9}. That miss is recorded
as REINJECT evidence; this module encodes the corrected invariant.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Box = Tuple[int, int, int, int]  # r0, r1, c0, c1 inclusive


def _majority_tile(seq: Sequence[Any]) -> Optional[Tuple[List[Any], List[Any], int, int]]:
    n = len(seq)
    best: Optional[Tuple[Tuple[int, int, int], List[Any], List[Any], int, int]] = None
    for period in range(1, max(1, n // 2) + 1):
        if n // period < 2:
            continue
        groups = [Counter() for _ in range(period)]
        for index, value in enumerate(seq):
            groups[index % period][value] += 1
        motif: List[Any] = []
        ambiguous = 0
        for group in groups:
            top = group.most_common(2)
            motif.append(top[0][0])
            if len(top) > 1 and top[0][1] == top[1][1]:
                ambiguous = 1
        repaired = [motif[index % period] for index in range(n)]
        mismatches = sum(a != b for a, b in zip(seq, repaired))
        key = (mismatches, ambiguous, period)
        if best is None or key < best[0]:
            best = (key, repaired, motif, period, mismatches)
    if best is None:
        return None
    _key, repaired, motif, period, mismatches = best
    return repaired, motif, period, mismatches


def _repair_sequence(
    seq: Sequence[int], max_frac: float = 0.35
) -> Optional[List[int]]:
    tiled = _majority_tile(seq)
    if tiled is None:
        return None
    repaired, _motif, _period, mismatches = tiled
    if mismatches == 0:
        return None
    if mismatches > max(1, int(len(seq) * max_frac)):
        return None
    return list(repaired)


def _frame_color(grid: Grid) -> int:
    height, width = len(grid), len(grid[0])
    border: List[int] = []
    for col in range(width):
        border.extend([grid[0][col], grid[height - 1][col]])
    for row in range(height):
        border.extend([grid[row][0], grid[row][width - 1]])
    return Counter(border).most_common(1)[0][0]


def _sep_row_panels(grid: Grid, frame: int) -> List[Box]:
    height, width = len(grid), len(grid[0])
    sep = [row for row in range(height) if all(value == frame for value in grid[row])]
    if len(sep) < 2:
        return []
    bounds = [-1] + sep + [height]
    panels: List[Box] = []
    for top, bottom in zip(bounds, bounds[1:]):
        if bottom - top > 1:
            panels.append((top + 1, bottom - 1, 0, width - 1))
    return panels


def _color3_column_blocks(grid: Grid) -> List[Box]:
    height, width = len(grid), len(grid[0])
    for row in range(height):
        if 3 not in grid[row]:
            continue
        col = 0
        runs: List[Tuple[int, int]] = []
        while col < width:
            if grid[row][col] == 3:
                start = col
                while col < width and grid[row][col] == 3:
                    col += 1
                if col - start >= 3:
                    runs.append((start, col - 1))
            else:
                col += 1
        if len(runs) < 2:
            continue
        for bottom in range(row + 2, height):
            if not all(
                grid[bottom][c] == 3 for start, end in runs for c in range(start, end + 1)
            ):
                continue
            ok = True
            for start, end in runs:
                span = bottom - row + 1
                if sum(grid[r][start] == 3 for r in range(row, bottom + 1)) < span // 2:
                    ok = False
                if sum(grid[r][end] == 3 for r in range(row, bottom + 1)) < span // 2:
                    ok = False
            if ok:
                return [(row, bottom, start, end) for start, end in runs]
    return []


def _repair_sep_panel(grid: Grid, box: Box) -> Tuple[Grid, bool]:
    r0, r1, c0, c1 = box
    out = [list(row) for row in grid]
    left, right = c0, c1

    def col_const(col: int) -> bool:
        return len({out[row][col] for row in range(r0, r1 + 1)}) == 1

    while left < right and col_const(left):
        left += 1
    while right > left and col_const(right):
        right -= 1
    changed = False
    for row in range(r0, r1 + 1):
        seq = out[row][left : right + 1]
        if len(seq) < 4 or len(set(seq)) <= 1:
            continue
        repaired = _repair_sequence(seq)
        if repaired is None:
            continue
        out[row][left : right + 1] = repaired
        changed = True
    return out, changed


def _repair_col3_block(grid: Grid, box: Box) -> Tuple[Grid, bool]:
    r0, r1, c0, c1 = box
    out = [list(row) for row in grid]
    top, bottom, left, right = r0 + 1, r1 - 1, c0 + 1, c1 - 1
    if top > bottom or left > right:
        return out, False
    rows = list(range(top, bottom + 1))
    sigs = [tuple(out[row][left : right + 1]) for row in rows]
    tiled = _majority_tile(sigs)
    if tiled is None:
        return out, False
    repaired, _motif, _period, mismatches = tiled
    if mismatches == 0:
        return out, False
    if mismatches > max(2, len(sigs) // 8):
        return out, False
    changed = False
    for index, row in enumerate(rows):
        if repaired[index] != sigs[index]:
            out[row][left : right + 1] = list(repaired[index])
            changed = True
    return out, changed


def transform(grid: Grid) -> Grid:
    frame = _frame_color(grid)
    col_blocks = _color3_column_blocks(grid)
    sep_panels = _sep_row_panels(grid, frame)
    use_cols = len(col_blocks) >= 2
    use_sep = len(sep_panels) >= 2 and not use_cols
    if not use_cols and not use_sep:
        if sep_panels:
            use_sep = True
        elif col_blocks:
            use_cols = True
    out = [list(row) for row in grid]
    if use_cols:
        for box in col_blocks:
            candidate, changed = _repair_col3_block(out, box)
            if changed:
                out = candidate
        return out
    for box in sep_panels:
        candidate, changed = _repair_sep_panel(out, box)
        if changed:
            out = candidate
    return out


def exact_candidates(train: List[Dict[str, Any]]) -> List[Tuple[str, Any]]:
    if not train:
        return []
    if all(transform(ex["input"]) == ex["output"] for ex in train):
        return [("container_period_tiling", transform)]
    return []


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    train = task.get("train") or []
    exact = exact_candidates(train)
    if not exact:
        passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
        return {
            "engine": "container_period_tiling",
            "train_replay": f"{passed}/{len(train)}",
            "perfect": False,
            "passed": passed,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, _transform = exact[0]
    passed = len(train)
    return {
        "engine": "container_period_tiling",
        "train_replay": f"{passed}/{len(train)}",
        "perfect": True,
        "passed": passed,
        "total": len(train),
        "licensed_transforms": [name],
        "primary_transform": name,
    }


def solve_task(task: Dict[str, Any]) -> Optional[List[Dict[str, Grid]]]:
    replay = train_replay(task)
    if not replay["perfect"]:
        return None
    attempts: List[Dict[str, Grid]] = []
    for case in task.get("test", []):
        pred = transform(case["input"])
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
    "solve_task",
    "submission_fragment",
    "train_replay",
    "transform",
]
