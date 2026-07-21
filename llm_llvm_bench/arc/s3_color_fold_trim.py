"""S3 color fold trim language game (FoT).

Grammar family owned here:
  color_fold_trim (canonical: eval task 8e5c0c38)
    S3 per-color horizontal fold trim; axis ties prefer smaller axis2.
    C4: licensed only on perfect train replay.

Core transform adapted from public solver with labeled-eval heal.
Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from collections import Counter, defaultdict
from typing import Callable, Dict, Iterable, List, Sequence, Tuple, TypeVar

Grid = List[List[int]]
Pos = Tuple[int, int]
T = TypeVar("T")


def fold_repaint(canvas: Grid, items: Sequence[T], update: Callable[[Grid, T], Grid]) -> Grid:
    acc = canvas
    for x in items:
        acc = update(acc, x)
    return acc


def background_color(grid: Grid) -> int:
    return Counter(pixel for row in grid for pixel in row).most_common(1)[0][0]


def groupCellsByColor(grid: Grid) -> Dict[int, List[Pos]]:
    bg = background_color(grid)
    groups: Dict[int, List[Pos]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != bg:
                groups[value].append((r, c))
    return groups


def evaluateAxisCost(cells: Sequence[Pos]) -> int:
    min_c = min(c for _, c in cells)
    max_c = max(c for _, c in cells)
    cells_set = set(cells)
    preferred_axis2 = min_c + max_c

    best_key = None
    best_axis2 = preferred_axis2

    for axis2 in range(2 * min_c, 2 * max_c + 1):
        to_remove = [
            (r, c) for (r, c) in cells if (r, axis2 - c) not in cells_set
        ]
        key = (len(to_remove), axis2)  # prefer smaller axis on delete-count ties
        if best_key is None or key < best_key:
            best_key = key
            best_axis2 = axis2

    return best_axis2


def trimAsymmetricCells(canvas: Grid, cells: Sequence[Pos], axis2: int) -> Grid:
    if not cells:
        return canvas
    bg = background_color(canvas)
    cells_set = set(cells)
    to_remove = [(r, c) for (r, c) in cells if (r, axis2 - c) not in cells_set]
    if not to_remove:
        return canvas
    out = [row[:] for row in canvas]
    for r, c in to_remove:
        out[r][c] = bg
    return out


def solve_8e5c0c38(grid: Grid) -> Grid:
    colour_groups = groupCellsByColor(grid)

    def trim(canvas: Grid, entry):
        colour, cells = entry
        axis = evaluateAxisCost(cells)
        return trimAsymmetricCells(canvas, cells, axis)

    trimmed = fold_repaint(grid, list(colour_groups.items()), trim)
    return trimmed

def color_fold_trim(grid: Grid) -> Grid:
    return solve_8e5c0c38(grid)


def named_candidates():
    return [("color_fold_trim", color_fold_trim)]


def exact_candidates(train):
    matched = []
    for name, transform in named_candidates():
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
            "engine": "s3_color_fold_trim",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_color_fold_trim",
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


__all__ = ["applies", "color_fold_trim", "exact_candidates", "named_candidates", "solve_8e5c0c38", "solve_task", "submission_fragment", "train_replay"]
