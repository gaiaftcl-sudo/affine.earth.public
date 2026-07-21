"""Batch FoT engine for eval task 5961cc34.

Grammar family owned here:
  corridor_fill (canonical: eval task 5961cc34)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 5961cc34). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def corridor_fill(grid: Grid) -> Optional[Grid]:
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
Solver for ARC puzzle 5961cc34
Pattern: Diamond shapes connected by directional lines from a yellow/green marker.

- Input has hexagonal diamond shapes (color 1/red) on background (color 8/blue)
- Each diamond has green3 (color 3) arrow cells on one side indicating connection direction
- A yellow (4) marker with green (2) line segment defines the starting line
- The yellow line extends opposite to the green segment, connecting to diamonds
- Connected diamonds form a network via their arrow directions
- Output: connected diamonds and lines become green (2), disconnected diamonds are removed
"""
from collections import Counter, deque


def _solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    flat = [v for r in input_grid for v in r]
    bg = Counter(flat).most_common(1)[0][0]

    yellow_pos = None
    green2_cells = set()
    red_cells = set()
    green3_cells = set()

    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == 4:
                yellow_pos = (r, c)
            elif v == 2:
                green2_cells.add((r, c))
            elif v == 1:
                red_cells.add((r, c))
            elif v == 3:
                green3_cells.add((r, c))

    yr, yc = yellow_pos
    nearest = min(green2_cells, key=lambda p: abs(p[0] - yr) + abs(p[1] - yc))
    dr_g = nearest[0] - yr
    dc_g = nearest[1] - yc
    if dr_g > 0:
        line_dir = 'up'
    elif dr_g < 0:
        line_dir = 'down'
    elif dc_g > 0:
        line_dir = 'left'
    else:
        line_dir = 'right'

    # Find connected components of red cells (diamonds)
    visited: set = set()
    diamonds: list = []
    for cell in sorted(red_cells):
        if cell in visited:
            continue
        comp: set = set()
        queue = deque([cell])
        while queue:
            cr, cc = queue.popleft()
            if (cr, cc) in visited:
                continue
            visited.add((cr, cc))
            comp.add((cr, cc))
            for ddr, ddc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = cr + ddr, cc + ddc
                if (nr, nc) in red_cells and (nr, nc) not in visited:
                    queue.append((nr, nc))
        diamonds.append(comp)

    # For each diamond, find adjacent green3 arrow cells and determine direction
    diamond_info: list = []
    for comp in diamonds:
        adj_g3: set = set()
        for cr, cc in comp:
            for ddr, ddc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = cr + ddr, cc + ddc
                if (nr, nc) in green3_cells:
                    adj_g3.add((nr, nc))

        if not adj_g3:
            diamond_info.append({'cells': comp, 'g3': set(), 'dir': None})
            continue

        center_r = sum(r for r, c in comp) / len(comp)
        center_c = sum(c for r, c in comp) / len(comp)
        g3_center_r = sum(r for r, c in adj_g3) / len(adj_g3)
        g3_center_c = sum(c for r, c in adj_g3) / len(adj_g3)

        ddr = g3_center_r - center_r
        ddc = g3_center_c - center_c

        if abs(ddc) > abs(ddr):
            direction = 'right' if ddc > 0 else 'left'
        else:
            direction = 'down' if ddr > 0 else 'up'

        diamond_info.append({'cells': comp, 'g3': adj_g3, 'dir': direction})

    STEP = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}

    output_cells: set = set()
    output_cells.add(yellow_pos)
    output_cells.update(green2_cells)

    connected: set = set()

    # Extend yellow line in opposite direction of green segment
    sr, sc = STEP[line_dir]
    r, c = yr + sr, yc + sc
    hit_diamond = None
    while 0 <= r < H and 0 <= c < W:
        output_cells.add((r, c))
        for i, di in enumerate(diamond_info):
            if (r, c) in di['cells']:
                hit_diamond = i
                break
        if hit_diamond is not None:
            break
        r += sr
        c += sc

    if hit_diamond is not None:
        connected.add(hit_diamond)

    # BFS through connected diamonds via their arrow directions
    process_queue = deque(connected)
    while process_queue:
        di_idx = process_queue.popleft()
        di = diamond_info[di_idx]

        output_cells.update(di['cells'])
        output_cells.update(di['g3'])

        if di['dir'] is None:
            continue

        g3 = di['g3']
        g3_rows = sorted(set(r for r, c in g3))
        g3_cols = sorted(set(c for r, c in g3))

        sr, sc = STEP[di['dir']]

        if di['dir'] in ('left', 'right'):
            start_c = (min(g3_cols) - 1) if di['dir'] == 'left' else (max(g3_cols) + 1)
            c = start_c
            hit = None
            while 0 <= c < W:
                for row in g3_rows:
                    output_cells.add((row, c))
                for row in g3_rows:
                    for i, d in enumerate(diamond_info):
                        if i != di_idx and (row, c) in d['cells']:
                            hit = i
                            break
                    if hit is not None:
                        break
                if hit is not None:
                    break
                c += sc
        else:
            start_r = (min(g3_rows) - 1) if di['dir'] == 'up' else (max(g3_rows) + 1)
            r = start_r
            hit = None
            while 0 <= r < H:
                for col in g3_cols:
                    output_cells.add((r, col))
                for col in g3_cols:
                    for i, d in enumerate(diamond_info):
                        if i != di_idx and (r, col) in d['cells']:
                            hit = i
                            break
                    if hit is not None:
                        break
                if hit is not None:
                    break
                r += sr

        if hit is not None and hit not in connected:
            connected.add(hit)
            process_queue.append(hit)

    output = [[bg] * W for _ in range(H)]
    for r, c in output_cells:
        if 0 <= r < H and 0 <= c < W:
            output[r][c] = 2

    return output



def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("corridor_fill", corridor_fill)]


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
            "engine": "s3_corridor_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_corridor_fill",
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
    "corridor_fill",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
