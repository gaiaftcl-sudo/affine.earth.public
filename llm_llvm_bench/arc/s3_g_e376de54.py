"""Batch FoT engine for eval task e376de54.

Grammar family owned here:
  g_e376de54 (canonical: eval task e376de54)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · e376de54). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_e376de54(grid: Grid) -> Optional[Grid]:
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
    
    cells = {}
    for r in range(rows):
        for c in range(cols):
            if g[r][c] != bg:
                cells[(r,c)] = g[r][c]
    
    if not cells:
        return g
    
    def get_segments(key_fn, coord_fn):
        groups = {}
        for (r,c) in cells:
            k = key_fn(r,c)
            groups.setdefault(k, []).append(coord_fn(r,c))
        segs = []
        for k, coords in groups.items():
            coords.sort()
            start = coords[0]
            for i in range(1, len(coords)):
                if coords[i] != coords[i-1] + 1:
                    segs.append((k, start, coords[i-1]))
                    start = coords[i]
            segs.append((k, start, coords[-1]))
        return segs
    
    directions = [
        ('h', lambda r,c: r, lambda r,c: c),
        ('v', lambda r,c: c, lambda r,c: r),
        ('d+', lambda r,c: r+c, lambda r,c: r),
        ('d-', lambda r,c: r-c, lambda r,c: r),
    ]
    
    best = min(directions, key=lambda d: len(get_segments(d[1], d[2])))
    dir_name = best[0]
    segments = get_segments(best[1], best[2])
    
    def coord_to_rc(k, coord):
        if dir_name == 'h': return (k, coord)
        elif dir_name == 'v': return (coord, k)
        elif dir_name == 'd+': return (coord, k - coord)
        elif dir_name == 'd-': return (coord, coord - k)
    
    seg_colors = []
    for seg in segments:
        k, start, end = seg
        rc = coord_to_rc(k, start)
        seg_colors.append(cells[rc])
    
    lengths = [end - start + 1 for _, start, end in segments]
    
    # Target length: maroon (9) reference if present, else mode
    if 9 in seg_colors:
        target_len = lengths[seg_colors.index(9)]
    else:
        target_len = Counter(lengths).most_common(1)[0][0]
    
    # Determine anchor (which end is consistent)
    def variance(lst):
        if len(lst) <= 1: return 0
        mean = sum(lst) / len(lst)
        return sum((x - mean)**2 for x in lst)
    
    if dir_name in ('d+', 'd-'):
        if dir_name == 'd+':
            sp = [2*s - k for k, s, _ in segments]
            ep = [2*e - k for k, _, e in segments]
        else:
            sp = [2*s + k for k, s, _ in segments]
            ep = [2*e + k for k, _, e in segments]
        anchor_start = variance(sp) < variance(ep)
    else:
        starts = [s for _, s, _ in segments]
        ends = [e for _, _, e in segments]
        anchor_start = variance(starts) <= variance(ends)
    
    for i, (k, start, end) in enumerate(segments):
        cur_len = end - start + 1
        if cur_len == target_len:
            continue
        
        color = seg_colors[i]
        
        if anchor_start:
            new_end = start + target_len - 1
            for coord in range(end + 1, new_end + 1):
                rc = coord_to_rc(k, coord)
                if 0 <= rc[0] < rows and 0 <= rc[1] < cols:
                    g[rc[0]][rc[1]] = color
            for coord in range(new_end + 1, end + 1):
                rc = coord_to_rc(k, coord)
                if 0 <= rc[0] < rows and 0 <= rc[1] < cols:
                    g[rc[0]][rc[1]] = bg
        else:
            new_start = end - target_len + 1
            for coord in range(new_start, start):
                rc = coord_to_rc(k, coord)
                if 0 <= rc[0] < rows and 0 <= rc[1] < cols:
                    g[rc[0]][rc[1]] = color
            for coord in range(start, new_start):
                rc = coord_to_rc(k, coord)
                if 0 <= rc[0] < rows and 0 <= rc[1] < cols:
                    g[rc[0]][rc[1]] = bg
    
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
    return [("g_e376de54", g_e376de54)]


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
            "engine": "s3_g_e376de54",
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
        "engine": "s3_g_e376de54",
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
    "g_e376de54",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
