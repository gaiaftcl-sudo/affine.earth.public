"""S2 marker-stripe lattice language game (FoT).

Grammar family owned here:
  marker_stripe_lattice (canonical: eval task 221dfab4)
    S1: same canvas shape (in-place palette rewrite).
    S2: color-4 marker forms a contiguous horizontal or vertical stripe.
    S3: on the marker-aligned parity lattice, paint cycle [4,4,3] by
        half-step distance from the marker; 4-steps fill marker cols/rows;
        3-steps paint marker stripe ∪ foreground cells; off-parity stripe
        cells clear to majority background.
    S4: vertical markers = transpose of the horizontal rule.
    C4: licensed only on perfect train replay.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _transpose(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid)]


def _solve_horizontal(grid: Grid) -> Optional[Grid]:
    height, width = len(grid), len(grid[0])
    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    markers = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 4]
    if not markers:
        return None
    marker_rows = sorted({r for r, _ in markers})
    marker_cols = sorted({c for _, c in markers})
    if len(marker_rows) != 1:
        return None
    marker_row = marker_rows[0]
    col0, col1 = marker_cols[0], marker_cols[-1] + 1
    # Marker must be a contiguous run.
    if marker_cols != list(range(col0, col1)):
        return None
    out = [list(row) for row in grid]
    for row in range(height):
        if (row - marker_row) % 2 != 0:
            for col in range(col0, col1):
                out[row][col] = background
            continue
        paint = [4, 4, 3][(abs(row - marker_row) // 2) % 3]
        if paint == 4:
            for col in range(col0, col1):
                out[row][col] = 4
        else:
            for col in range(width):
                if col0 <= col < col1 or (
                    grid[row][col] != background and grid[row][col] != 4
                ):
                    out[row][col] = 3
    return out


def marker_stripe_lattice(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    height, width = len(grid), len(grid[0])
    markers = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 4]
    if not markers:
        return None
    marker_rows = sorted({r for r, _ in markers})
    marker_cols = sorted({c for _, c in markers})
    if len(marker_rows) == 1:
        return _solve_horizontal(grid)
    if len(marker_cols) == 1:
        # Contiguous vertical run.
        row0, row1 = marker_rows[0], marker_rows[-1] + 1
        if marker_rows != list(range(row0, row1)):
            return None
        transposed = _solve_horizontal(_transpose(grid))
        if transposed is None:
            return None
        return _transpose(transposed)
    return None


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("marker_stripe_lattice", marker_stripe_lattice)]


def exact_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    matched: List[Tuple[str, Transform]] = []
    for name, transform in named_candidates(train):
        try:
            if all(transform(example["input"]) == example["output"] for example in train):
                matched.append((name, transform))
        except Exception:
            continue
    return matched


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    train = task.get("train", [])
    exact = exact_candidates(train)
    if not exact:
        return {
            "engine": "s2_marker_stripe_lattice",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_marker_stripe_lattice",
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
    "marker_stripe_lattice",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
