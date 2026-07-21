"""Batch FoT engine for eval task eee78d87.

Grammar family owned here:
  g_eee78d87 (canonical: eval task eee78d87)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · eee78d87). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_eee78d87(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


"""Solver for eee78d87 — 3x3 Pattern Tiling with Maroon Center
6x6 input → 16x16 tiled output. Non-bg cells define a 3x3 tile (mod 3).
The tile is tiled across the 16x16 output, offset by the pattern center.
Center 6x6 region has black→maroon replacement."""
import json
from collections import Counter
from typing import List

def solve(grid: List[List[int]]) -> List[List[int]]:
    flat = [v for row in grid for v in row]
    bg = Counter(flat).most_common(1)[0][0]
    tile = [[bg]*3 for _ in range(3)]
    non_bg = []
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] != bg:
                tile[r%3][c%3] = 0
                non_bg.append((r, c))
    cr = ((min(r for r,_ in non_bg) + max(r for r,_ in non_bg)) // 2) % 3
    cc = ((min(c for _,c in non_bg) + max(c for _,c in non_bg)) // 2) % 3
    out = [[0]*16 for _ in range(16)]
    for r in range(16):
        for c in range(16):
            v = tile[(r+cr)%3][(c+cc)%3]
            if 5<=r<=10 and 5<=c<=10 and v==0: v = 9
            out[r][c] = v
    return out

if __name__ == '__main__':
    import sys
    with open(sys.argv[1]) as f: task = json.load(f)
    for i, ex in enumerate(task['train']):
        print(f"Train {i}: {'PASS ✓' if solve(ex['input'])==ex['output'] else 'FAIL'}")
    for i, ex in enumerate(task['test']):
        print(f"Test {i}: {json.dumps(solve(ex['input']))}")



def _solve(grid: Grid):
    return solve(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_eee78d87", g_eee78d87)]


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
            "engine": "s3_g_eee78d87",
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
        "engine": "s3_g_eee78d87",
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
    "g_eee78d87",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
