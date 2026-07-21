"""Batch FoT engine for eval task 8b7bacbf.

Grammar family owned here:
  g_8b7bacbf (canonical: eval task 8b7bacbf)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 8b7bacbf). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_8b7bacbf(grid: Grid) -> Optional[Grid]:
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
8b7bacbf — Fill frame interiors connected to dot through chain network

Pattern:
- Grid has rectangular/diamond frames made of colored cells
- Chains of connecting-color cells link frames together
- One or more uniquely-colored dots sit in the network
- Rule: fill interior of frames with the color of the dot whose chain reaches them

Algorithm:
1. Detect bg (most common color), find all dots (isolated non-bg cells
   with no same-color and no bg 4-neighbors)
2. For each dot, identify its chain color (non-bg non-dot 4-neighbor colors)
3. Build chain_color → dot_color mapping
4. Build c_dot: all non-bg cells 8-connected to any dot
5. Find enclosed bg regions via corner-seeded flood fill
6. Fill region if its boundary is in c_dot, contains no chain-color cells,
   and is 8-adj to a chain-color cell in c_dot — using that chain's dot color
"""
import json
from collections import deque, Counter


def solve(grid: list[list[int]]) -> list[list[int]]:
    rows, cols = len(grid), len(grid[0])
    g = [row[:] for row in grid]

    # Detect background: most common color
    counts: Counter = Counter()
    for row in g:
        counts.update(row)
    bg = counts.most_common(1)[0][0]

    # Find all dots: non-bg cells with no same-color and no bg 4-neighbors
    dots: list[tuple[tuple[int, int], int]] = []
    for r in range(rows):
        for c in range(cols):
            v = g[r][c]
            if v == bg:
                continue
            same_count = bg_count = 0
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    if g[nr][nc] == v:
                        same_count += 1
                    if g[nr][nc] == bg:
                        bg_count += 1
            if same_count == 0 and bg_count == 0:
                dots.append(((r, c), v))

    if not dots:
        return g

    # Build chain_color → dot_color mapping
    chain_to_fill: dict[int, int] = {}
    for (dr2, dc2), d_color in dots:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = dr2 + dr, dc2 + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                cc = g[nr][nc]
                if cc != bg and cc != d_color:
                    chain_to_fill[cc] = d_color

    # Build c_dot: all non-bg cells 8-connected to any dot
    c_dot: set[tuple[int, int]] = set()
    q: deque = deque([pos for pos, _ in dots])
    while q:
        r, c = q.popleft()
        if (r, c) in c_dot:
            continue
        c_dot.add((r, c))
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    if (nr, nc) not in c_dot and g[nr][nc] != bg:
                        q.append((nr, nc))

    # Find enclosed bg regions via corner-seeded flood fill
    exterior: set[tuple[int, int]] = set()
    q = deque()
    for sr, sc in [(0, 0), (0, cols - 1), (rows - 1, 0), (rows - 1, cols - 1)]:
        if g[sr][sc] == bg:
            q.append((sr, sc))
    while q:
        r, c = q.popleft()
        if (r, c) in exterior:
            continue
        exterior.add((r, c))
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if (nr, nc) not in exterior and g[nr][nc] == bg:
                    q.append((nr, nc))

    # Process each enclosed bg region
    visited_bg: set[tuple[int, int]] = set()
    for r in range(rows):
        for c in range(cols):
            if g[r][c] != bg or (r, c) in exterior or (r, c) in visited_bg:
                continue
            region: set[tuple[int, int]] = set()
            boundary: set[tuple[int, int]] = set()
            q2: deque = deque([(r, c)])
            while q2:
                rr, cc = q2.popleft()
                if (rr, cc) in region:
                    continue
                region.add((rr, cc))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if g[nr][nc] == bg and (nr, nc) not in region and (nr, nc) not in exterior:
                            q2.append((nr, nc))
                        elif g[nr][nc] != bg:
                            boundary.add((nr, nc))
            visited_bg |= region

            # Check 1: boundary connected to dot network
            if not any(b in c_dot for b in boundary):
                continue

            # Try each chain color to find the right fill
            fill_color = None
            for chain_c, dot_c in chain_to_fill.items():
                # Check 2: boundary has no cells of this chain color
                if any(g[br][bc] == chain_c for br, bc in boundary):
                    continue

                # Check 3: boundary 8-adj to a cell of this chain color in c_dot
                has_chain_link = False
                for br, bc in boundary:
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = br + dr, bc + dc
                            if 0 <= nr < rows and 0 <= nc < cols:
                                if g[nr][nc] == chain_c and (nr, nc) in c_dot and (nr, nc) not in boundary:
                                    has_chain_link = True
                                    break
                        if has_chain_link:
                            break
                    if has_chain_link:
                        break

                if has_chain_link:
                    fill_color = dot_c
                    break

            if fill_color is not None:
                for rr, cc in region:
                    g[rr][cc] = fill_color

    return g


if __name__ == "__main__":
    import sys
    with open(sys.argv[1]) as f:
        task = json.load(f)
    for i, ex in enumerate(task["train"]):
        result = solve(ex["input"])
        match = result == ex["output"]
        print(f"Train {i}: {'PASS' if match else 'FAIL'}")



def _solve(grid: Grid):
    return solve(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_8b7bacbf", g_8b7bacbf)]


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
            "engine": "s3_g_8b7bacbf",
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
        "engine": "s3_g_8b7bacbf",
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
    "g_8b7bacbf",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
