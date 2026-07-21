"""Batch FoT engine for eval task 88e364bc.

Grammar family owned here:
  g_88e364bc (canonical: eval task 88e364bc)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 88e364bc). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_88e364bc(grid: Grid) -> Optional[Grid]:
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
Solver for ARC-AGI task 88e364bc.

Pattern: Each grid has "template" rectangles (solid non-zero blocks with 1s and 2s
inside) and irregular enclosed shapes of the same border colors containing yellow
markers (4). The position of the 2s in a template relative to its center defines
a compass direction. Each 4 slides in that direction until it hits the wall of its
enclosing shape.
"""

import json


def solve(grid):
    rows = len(grid)
    cols = len(grid[0])

    # --- Step 1: Find templates via BFS from cells with value 2 ---
    templates = {}  # border_color -> (dr, dc) direction
    visited = set()

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 2 and (r, c) not in visited:
                # BFS through all non-zero, non-4 cells
                component = []
                seen = set()
                queue = [(r, c)]
                while queue:
                    cr, cc = queue.pop(0)
                    if (cr, cc) in seen:
                        continue
                    if not (0 <= cr < rows and 0 <= cc < cols):
                        continue
                    if grid[cr][cc] == 0 or grid[cr][cc] == 4:
                        continue
                    seen.add((cr, cc))
                    component.append((cr, cc))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        if (cr + dr, cc + dc) not in seen:
                            queue.append((cr + dr, cc + dc))

                visited |= seen

                min_r = min(r for r, _ in component)
                max_r = max(r for r, _ in component)
                min_c = min(c for _, c in component)
                max_c = max(c for _, c in component)

                # Templates are solid rectangles (no 0-gaps inside)
                expected = (max_r - min_r + 1) * (max_c - min_c + 1)
                if len(component) != expected:
                    continue

                border_color = grid[min_r][min_c]

                # Collect 2-positions in local coordinates
                twos = [
                    (tr - min_r, tc - min_c)
                    for tr, tc in component
                    if grid[tr][tc] == 2
                ]

                center_r = (max_r - min_r) / 2.0
                center_c = (max_c - min_c) / 2.0
                avg_r = sum(r for r, _ in twos) / len(twos)
                avg_c = sum(c for _, c in twos) / len(twos)

                def sign(x):
                    return 1 if x > 0.01 else (-1 if x < -0.01 else 0)

                templates[border_color] = (sign(avg_r - center_r), sign(avg_c - center_c))

    # --- Step 2: For each 4, find enclosing color, then slide ---
    fours = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 4]
    result = [row[:] for row in grid]

    for r, c in fours:
        # Scan 4 cardinal directions to find nearest wall color
        best_dist = float("inf")
        color = None
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc, d = r + dr, c + dc, 1
            while 0 <= nr < rows and 0 <= nc < cols:
                v = grid[nr][nc]
                if v != 0 and v != 4:
                    if d < best_dist:
                        best_dist = d
                        color = v
                    break
                nr += dr
                nc += dc
                d += 1

        if color is None or color not in templates:
            continue

        move_dr, move_dc = templates[color]
        result[r][c] = 0

        # Slide until hitting a wall (diagonal moves can't squeeze through corners)
        nr, nc = r, c
        while True:
            nnr, nnc = nr + move_dr, nc + move_dc
            if not (0 <= nnr < rows and 0 <= nnc < cols and grid[nnr][nnc] in (0, 4)):
                break
            if move_dr != 0 and move_dc != 0:
                if not (0 <= nr + move_dr < rows and grid[nr + move_dr][nc] in (0, 4)):
                    break
                if not (0 <= nc + move_dc < cols and grid[nr][nc + move_dc] in (0, 4)):
                    break
            nr, nc = nnr, nnc

        result[nr][nc] = 4

    return result


if __name__ == "__main__":
    with open("/Users/evanpieser/arc-puzzle-catalog/dataset/tasks/88e364bc.json") as f:
        task = json.load(f)

    all_pass = True
    for i, pair in enumerate(task["train"]):
        output = solve(pair["input"])
        expected = pair["output"]
        if output == expected:
            print(f"Train {i}: PASS")
        else:
            all_pass = False
            print(f"Train {i}: FAIL")
            for r in range(len(expected)):
                for c in range(len(expected[0])):
                    if output[r][c] != expected[r][c]:
                        print(f"  ({r},{c}): expected {expected[r][c]}, got {output[r][c]}")

    for i, pair in enumerate(task["test"]):
        output = solve(pair["input"])
        if "output" in pair:
            expected = pair["output"]
            if output == expected:
                print(f"Test {i}: PASS")
            else:
                all_pass = False
                print(f"Test {i}: FAIL")
                for r in range(len(expected)):
                    for c in range(len(expected[0])):
                        if output[r][c] != expected[r][c]:
                            print(f"  ({r},{c}): expected {expected[r][c]}, got {output[r][c]}")
        else:
            print(f"Test {i}: (no expected output)")

    print("\nALL PASS" if all_pass else "\nSOME FAILED")



def _solve(grid: Grid):
    return solve(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_88e364bc", g_88e364bc)]


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
            "engine": "s3_g_88e364bc",
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
        "engine": "s3_g_88e364bc",
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
    "g_88e364bc",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
