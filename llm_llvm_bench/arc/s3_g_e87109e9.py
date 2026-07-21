"""Batch FoT engine for eval task e87109e9.

Grammar family owned here:
  g_e87109e9 (canonical: eval task e87109e9)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · e87109e9). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_e87109e9(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


import json
import sys
from collections import Counter


def solve(grid):
    # Parse legend (top 6 rows): each of 4 boxes shows color on LEFT or RIGHT
    legend = {}
    for b in range(4):
        start_col = 1 + b * 6
        vals = grid[1][start_col:start_col + 4]
        for i, v in enumerate(vals):
            if v not in (0, 5):
                legend[v] = 'LEFT' if i == 0 else 'RIGHT'
                break

    lower = [row[:] for row in grid[6:]]
    H, W = len(lower), len(lower[0])
    bg = Counter(v for row in lower for v in row).most_common(1)[0][0]

    eight_cells = [(r, c) for r in range(H) for c in range(W) if lower[r][c] == 8]
    cr_min = min(r for r, c in eight_cells)
    cr_max = max(r for r, c in eight_cells)
    cc_min = min(c for r, c in eight_cells)
    cc_max = max(c for r, c in eight_cells)
    N = cr_max - cr_min + 1

    out = [row[:] for row in lower]
    visited = set()

    def get_turn(travel_dir, side):
        if side == 'LEFT':
            return {'UP': 'LEFT', 'DOWN': 'RIGHT', 'LEFT': 'DOWN', 'RIGHT': 'UP'}[travel_dir]
        return {'UP': 'RIGHT', 'DOWN': 'LEFT', 'LEFT': 'UP', 'RIGHT': 'DOWN'}[travel_dir]

    def extend(r0, r1, c0, c1, d):
        key = (r0, r1, c0, c1, d)
        if key in visited:
            return
        visited.add(key)

        if d == 'UP':
            hit, stop = None, 0
            for r in range(r0 - 1, -1, -1):
                for c in range(c0, c1 + 1):
                    if lower[r][c] != bg and lower[r][c] != 8:
                        hit, stop = lower[r][c], r + 1
                        break
                if hit:
                    break
            for r in range(stop, r0):
                for c in range(c0, c1 + 1):
                    out[r][c] = 8
            if hit and hit in legend:
                extend(stop, stop + N - 1, c0, c1, get_turn('UP', legend[hit]))

        elif d == 'DOWN':
            hit, stop = None, H - 1
            for r in range(r1 + 1, H):
                for c in range(c0, c1 + 1):
                    if lower[r][c] != bg and lower[r][c] != 8:
                        hit, stop = lower[r][c], r - 1
                        break
                if hit:
                    break
            for r in range(r1 + 1, stop + 1):
                for c in range(c0, c1 + 1):
                    out[r][c] = 8
            if hit and hit in legend:
                extend(stop - N + 1, stop, c0, c1, get_turn('DOWN', legend[hit]))

        elif d == 'LEFT':
            hit, stop = None, 0
            for c in range(c0 - 1, -1, -1):
                for r in range(r0, r1 + 1):
                    if lower[r][c] != bg and lower[r][c] != 8:
                        hit, stop = lower[r][c], c + 1
                        break
                if hit:
                    break
            for r in range(r0, r1 + 1):
                for c in range(stop, c0):
                    out[r][c] = 8
            if hit and hit in legend:
                extend(r0, r1, stop, stop + N - 1, get_turn('LEFT', legend[hit]))

        elif d == 'RIGHT':
            hit, stop = None, W - 1
            for c in range(c1 + 1, W):
                for r in range(r0, r1 + 1):
                    if lower[r][c] != bg and lower[r][c] != 8:
                        hit, stop = lower[r][c], c - 1
                        break
                if hit:
                    break
            for r in range(r0, r1 + 1):
                for c in range(c1 + 1, stop + 1):
                    out[r][c] = 8
            if hit and hit in legend:
                extend(r0, r1, stop - N + 1, stop, get_turn('RIGHT', legend[hit]))

    for d in ('UP', 'DOWN', 'LEFT', 'RIGHT'):
        extend(cr_min, cr_max, cc_min, cc_max, d)

    return out


if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        data = json.load(f)

    all_pass = True
    for split in ('train', 'test'):
        for i, ex in enumerate(data.get(split, [])):
            result = solve(ex['input'])
            expected = ex['output']
            ok = result == expected
            print(f'{split}[{i}]: {"PASS" if ok else "FAIL"}')
            if not ok:
                all_pass = False
                for r in range(min(len(result), len(expected))):
                    if result[r] != expected[r]:
                        print(f'  row {r}: got      {result[r]}')
                        print(f'  row {r}: expected {expected[r]}')



def _solve(grid: Grid):
    return solve(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_e87109e9", g_e87109e9)]


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
            "engine": "s3_g_e87109e9",
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
        "engine": "s3_g_e87109e9",
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
    "g_e87109e9",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
