"""Batch FoT engine for eval task c7f57c3e.

Grammar family owned here:
  g_c7f57c3e (canonical: eval task c7f57c3e)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · c7f57c3e). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_c7f57c3e(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


"""
ARC-AGI puzzle c7f57c3e solver.

Pattern: Each grid contains multiple objects sharing the same arm structure (color 1)
at different scales. Objects come in exactly two "variants" distinguished by their
non-arm colored cells (center color, extra element position/color). The transformation
swaps every object's variant to the other one.

Algorithm:
1. Flood-fill (8-connected) to find objects
2. For each object, compute arm bounding box and scale
3. Normalize non-arm cells to a unit template via integer division by scale
4. Group objects into two variant types
5. Redraw each object using the other variant's template (scaled back up)
"""

import json
import copy
from collections import Counter, defaultdict


def transform(grid):
    grid = [list(row) for row in grid]
    rows, cols = len(grid), len(grid[0])

    # Background = most common color
    bg = Counter(
        grid[r][c] for r in range(rows) for c in range(cols)
    ).most_common(1)[0][0]

    # 8-connected flood fill to find objects
    visited = [[False] * cols for _ in range(rows)]
    objects = []

    def flood_fill(sr, sc):
        stack = [(sr, sc)]
        cells = []
        while stack:
            r, c = stack.pop()
            if not (0 <= r < rows and 0 <= c < cols):
                continue
            if visited[r][c] or grid[r][c] == bg:
                continue
            visited[r][c] = True
            cells.append((r, c, grid[r][c]))
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr or dc:
                        stack.append((r + dr, c + dc))
        return cells

    for r in range(rows):
        for c in range(cols):
            if not visited[r][c] and grid[r][c] != bg:
                cells = flood_fill(r, c)
                if cells:
                    objects.append(cells)

    arm_color = 1

    # Compute arm bounding box and scale for each object
    obj_info = []
    for cells in objects:
        arms = [(r, c) for r, c, v in cells if v == arm_color]
        if not arms:
            continue
        ar0 = min(r for r, c in arms)
        ac0 = min(c for r, c in arms)
        ar1 = max(r for r, c in arms)
        ac1 = max(c for r, c in arms)
        obj_info.append({
            'cells': cells,
            'arm_origin': (ar0, ac0),
            'arm_h': ar1 - ar0 + 1,
            'arm_w': ac1 - ac0 + 1,
        })

    min_h = min(o['arm_h'] for o in obj_info)
    for o in obj_info:
        o['scale'] = o['arm_h'] // min_h

    # Normalize templates using floor division by scale
    for o in obj_info:
        s = o['scale']
        r0, c0 = o['arm_origin']
        tmpl = {}
        for r, c, v in o['cells']:
            tr, tc = (r - r0) // s, (c - c0) // s
            tmpl[(tr, tc)] = v
        o['template'] = tmpl
        o['variant'] = frozenset(
            (tr, tc, v) for (tr, tc), v in tmpl.items() if v != arm_color
        )

    # Group by variant — expect exactly 2
    groups = defaultdict(list)
    for i, o in enumerate(obj_info):
        groups[o['variant']].append(i)

    variants = list(groups.keys())
    assert len(variants) == 2, f"Expected 2 variants, got {len(variants)}"
    swap = {variants[0]: variants[1], variants[1]: variants[0]}

    # Apply swap: erase old non-arm cells, draw new variant
    result = copy.deepcopy(grid)
    for var, indices in groups.items():
        target = swap[var]
        for idx in indices:
            o = obj_info[idx]
            s = o['scale']
            r0, c0 = o['arm_origin']

            # Erase current non-arm cells
            for r, c, v in o['cells']:
                if v != arm_color:
                    result[r][c] = bg

            # Draw target variant (scaled)
            for tr, tc, v in target:
                for dr in range(s):
                    for dc in range(s):
                        nr, nc = r0 + tr * s + dr, c0 + tc * s + dc
                        if 0 <= nr < rows and 0 <= nc < cols:
                            result[nr][nc] = v

    return result



def _solve(grid: Grid):
    return transform(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_c7f57c3e", g_c7f57c3e)]


def exact_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    out: List[Tuple[str, Transform]] = []
    for name, transform in named_candidates():
        if all(transform(ex["input"]) == ex["output"] for ex in train):
            out.append((name, transform))
    return out


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    train = task.get("train", [])
    exact = exact_candidates(train)
    if not exact:
        return {
            "engine": "s3_g_c7f57c3e",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
            "primary_transform": None,
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_g_c7f57c3e",
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
    "g_c7f57c3e",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
