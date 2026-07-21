"""S3 period-lattice rewrite language game (FoT).

Grammar family owned here:
  period_lattice_rewrite (canonical: eval task 16de56c4)
    S1: same canvas shape (in-place spatial rewrite).
    S2: choose axis = rows if more multi-seed rows than multi-seed cols, else cols.
    S3: on each line with ≥2 nonzero seeds:
        - one color: period = gcd(gaps), phase = first_pos % period;
          paint every lattice cell on the full line;
        - pattern color (count≥2) + singleton (count==1):
            period/phase from pattern positions;
            if singleton lies on the lattice → recolor lattice in [min,max] seed span;
            else extend pattern on full lattice and keep the singleton.
    S4: lines with <2 seeds unchanged (filled by the orthogonal axis choice).
    C4: exact rewrite; licensed only when every training pair replays.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter
from functools import reduce
from math import gcd
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _transform_line(cells: Sequence[int]) -> List[int]:
    n = len(cells)
    seeds = [(i, cells[i]) for i in range(n) if cells[i] != 0]
    if len(seeds) < 2:
        return list(cells)
    counts = Counter(value for _, value in seeds)
    colors = list(counts.keys())
    result = [0] * n

    if len(colors) == 1:
        color = colors[0]
        positions = [pos for pos, _ in seeds]
        gaps = [positions[i + 1] - positions[i] for i in range(len(positions) - 1)]
        period = reduce(gcd, gaps)
        phase = positions[0] % period
        for i in range(n):
            if i % period == phase:
                result[i] = color
        return result

    pattern_colors = [color for color, count in counts.items() if count >= 2]
    singleton_colors = [color for color, count in counts.items() if count == 1]
    if len(pattern_colors) != 1 or len(singleton_colors) != 1:
        return list(cells)

    pattern_color = pattern_colors[0]
    singleton_color = singleton_colors[0]
    pattern_pos = [pos for pos, value in seeds if value == pattern_color]
    gaps = [pattern_pos[i + 1] - pattern_pos[i] for i in range(len(pattern_pos) - 1)]
    period = reduce(gcd, gaps) if gaps else 1
    phase = pattern_pos[0] % period
    singleton_pos = next(pos for pos, value in seeds if value == singleton_color)

    if singleton_pos % period == phase:
        min_pos = min(pos for pos, _ in seeds)
        max_pos = max(pos for pos, _ in seeds)
        for i in range(n):
            if i % period == phase and min_pos <= i <= max_pos:
                result[i] = singleton_color
        return result

    for i in range(n):
        if i % period == phase:
            result[i] = pattern_color
    result[singleton_pos] = singleton_color
    return result


def _multi_seed_lines(grid: Grid, axis: str) -> int:
    height, width = len(grid), len(grid[0])
    count = 0
    if axis == "row":
        for row in range(height):
            if sum(1 for col in range(width) if grid[row][col] != 0) >= 2:
                count += 1
    else:
        for col in range(width):
            if sum(1 for row in range(height) if grid[row][col] != 0) >= 2:
                count += 1
    return count


def _apply_rows(grid: Grid) -> Grid:
    return [_transform_line(row) for row in grid]


def _apply_cols(grid: Grid) -> Grid:
    height, width = len(grid), len(grid[0])
    columns = [[grid[row][col] for row in range(height)] for col in range(width)]
    rewritten = [_transform_line(column) for column in columns]
    return [[rewritten[col][row] for col in range(width)] for row in range(height)]


def period_lattice_rewrite(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    row_score = _multi_seed_lines(grid, "row")
    col_score = _multi_seed_lines(grid, "col")
    if row_score < 1 and col_score < 1:
        return None
    if col_score > row_score:
        return _apply_cols(grid)
    return _apply_rows(grid)


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("period_lattice_rewrite", period_lattice_rewrite)]


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
            "engine": "s3_period_lattice_rewrite",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_period_lattice_rewrite",
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
    "period_lattice_rewrite",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
