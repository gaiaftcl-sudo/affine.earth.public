"""Batch FoT engine for eval task 8e5c0c38.

Grammar family owned here:
  g_8e5c0c38 (canonical: eval task 8e5c0c38)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 8e5c0c38). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_8e5c0c38(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


import json, sys
from collections import Counter

def solve(grid):
    rows, cols = len(grid), len(grid[0])
    g = [row[:] for row in grid]
    
    all_vals = [g[r][c] for r in range(rows) for c in range(cols)]
    bg = Counter(all_vals).most_common(1)[0][0]
    
    by_color = {}
    for r in range(rows):
        for c in range(cols):
            if g[r][c] != bg:
                by_color.setdefault(g[r][c], set()).add((r,c))
    
    for color, comp in by_color.items():
        if len(comp) <= 2:
            continue
        
        # Find best LR axis only (vertical axis of symmetry)
        min_c = min(c for _,c in comp)
        max_c = max(c for _,c in comp)
        best_lr_count = len(comp) + 1
        best_lr_removals = set()
        for axis2 in range(2*min_c, 2*max_c + 1):
            removals = frozenset((r,c) for (r,c) in comp if (r, axis2-c) not in comp)
            if len(removals) < best_lr_count:
                best_lr_count = len(removals)
                best_lr_removals = removals
        
        for (r,c) in best_lr_removals:
            g[r][c] = bg
    
    return g

if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        task = json.load(f)

    for i, ex in enumerate(task['train']):
        result = solve(ex['input'])
        expected = ex['output']
        match = result == expected
        print(f"Train {i}: {'PASS' if match else 'FAIL'}")
        if not match:
            for r in range(len(expected)):
                for c in range(len(expected[0])):
                    if result[r][c] != expected[r][c]:
                        print(f"  ({r},{c}): got {result[r][c]}, expected {expected[r][c]}")



def _solve(grid: Grid):
    return solve(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_8e5c0c38", g_8e5c0c38)]


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
            "engine": "s3_g_8e5c0c38",
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
        "engine": "s3_g_8e5c0c38",
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
    "g_8e5c0c38",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
