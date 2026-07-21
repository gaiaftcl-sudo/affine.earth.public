"""S1 separator-row extent sort language game (FoT).

Grammar family owned here:
  sep_row_extent_sort (canonical: eval task 31f7f899)
    S1: majority/background is 8; separator is the row with the most 6s.
    S2: motif columns = sep-row cells that are neither bg nor 6.
    S3: each motif column has an input vertical extent = max |r-sep| among
        non-bg/non-6 cells in that column. Sort those extents ascending and
        reassign left→right onto motif columns.
    S4: clear to bg (keep all 6s + the sep row); paint each motif column's
        sep color vertically to its new extent, clipped to the input motif
        row bbox so bilateral paint cannot leave the observed band.
    C4: exact rewrite licensed by full train replay.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_BG = 8
_SEP_COLOR = 6


def sep_row_extent_sort(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    height, width = len(grid), len(grid[0])
    sep = max(
        range(height),
        key=lambda r: sum(1 for c in range(width) if grid[r][c] == _SEP_COLOR),
    )
    if not any(cell == _SEP_COLOR for cell in grid[sep]):
        return None
    row = grid[sep]
    motif_cols = [c for c in range(width) if row[c] not in (_BG, _SEP_COLOR)]
    if not motif_cols:
        return None

    extents: List[int] = []
    motif_rows: set[int] = set()
    for c in motif_cols:
        cells = [r for r in range(height) if grid[r][c] not in (_BG, _SEP_COLOR)]
        motif_rows.update(cells)
        extents.append(max((abs(r - sep) for r in cells), default=0))
    for r in range(height):
        for c in range(width):
            if grid[r][c] not in (_BG, _SEP_COLOR):
                motif_rows.add(r)
    if not motif_rows:
        return None
    row_min, row_max = min(motif_rows), max(motif_rows)
    targets = {c: ext for c, ext in zip(motif_cols, sorted(extents))}

    out: Grid = [[_BG] * width for _ in range(height)]
    for r in range(height):
        for c in range(width):
            if grid[r][c] == _SEP_COLOR:
                out[r][c] = _SEP_COLOR
    for c in range(width):
        out[sep][c] = row[c]
    for c in motif_cols:
        color = row[c]
        for dist in range(1, targets[c] + 1):
            for r in (sep - dist, sep + dist):
                if 0 <= r < height and row_min <= r <= row_max:
                    out[r][c] = color
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("sep_row_extent_sort", sep_row_extent_sort)]


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
            "engine": "s1_sep_row_extent_sort",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_sep_row_extent_sort",
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
    "sep_row_extent_sort",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
