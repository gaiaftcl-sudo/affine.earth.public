"""Batch FoT engine for eval task 7ed72f31.

Grammar family owned here:
  paired_recolor (canonical: eval task 7ed72f31)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 7ed72f31). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def paired_recolor(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


"""Solver for ARC-AGI task 7ed72f31.

Pattern: Each colored shape is 8-connected to a group of 2-cells that acts as
a reflection axis.  A single 2-cell triggers point reflection (180° rotation);
a horizontal line of 2s mirrors across its row; a vertical line mirrors across
its column.  The reflected copy is painted in the same color.
"""

import copy
import json
from collections import Counter, deque


def _solve(grid: list[list[int]]) -> list[list[int]]:
    rows, cols = len(grid), len(grid[0])
    output = copy.deepcopy(grid)

    # Background = most frequent value
    bg = Counter(v for row in grid for v in row).most_common(1)[0][0]

    # Collect non-background cells
    non_bg = {(r, c) for r in range(rows) for c in range(cols) if grid[r][c] != bg}

    # 8-connected components of non-background cells
    visited: set[tuple[int, int]] = set()
    components: list[set[tuple[int, int]]] = []
    for seed in non_bg:
        if seed in visited:
            continue
        comp: set[tuple[int, int]] = set()
        q = deque([seed])
        visited.add(seed)
        while q:
            r, c = q.popleft()
            comp.add((r, c))
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in non_bg and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        q.append((nr, nc))
        components.append(comp)

    for comp in components:
        twos = {p for p in comp if grid[p[0]][p[1]] == 2}
        shape = {p for p in comp if grid[p[0]][p[1]] != 2}
        if not twos or not shape:
            continue

        two_rows = {r for r, _ in twos}
        two_cols = {c for _, c in twos}

        if len(twos) == 1:
            # Point reflection
            r0, c0 = next(iter(twos))
            for r, c in shape:
                nr, nc = 2 * r0 - r, 2 * c0 - c
                if 0 <= nr < rows and 0 <= nc < cols:
                    output[nr][nc] = grid[r][c]
        elif len(two_rows) == 1:
            # Horizontal line → mirror across row
            r0 = next(iter(two_rows))
            for r, c in shape:
                nr = 2 * r0 - r
                if 0 <= nr < rows:
                    output[nr][c] = grid[r][c]
        elif len(two_cols) == 1:
            # Vertical line → mirror across column
            c0 = next(iter(two_cols))
            for r, c in shape:
                nc = 2 * c0 - c
                if 0 <= nc < cols:
                    output[r][nc] = grid[r][c]

    return output



def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("paired_recolor", paired_recolor)]


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
            "engine": "s2_paired_recolor",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_paired_recolor",
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
    "paired_recolor",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
