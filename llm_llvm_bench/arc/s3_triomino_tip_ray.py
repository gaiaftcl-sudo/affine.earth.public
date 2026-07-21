"""S3 triomino tip-ray language game (FoT).

Grammar family owned here:
  triomino_tip_ray (canonical: eval task 409aa875)
    S1: same canvas; majority color = background.
    S2: 8-connected non-bg components of size 3 are tip triominoes.
    S3: each tip fires a ray of length 5 along its tip direction.
    S4: landing cell: bg→9; occupied→recolor that component to 9;
        multi-ray collision→1.
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 409aa875). Never submits to Kaggle.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def triomino_tip_ray(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    if len(out) != len(grid) or len(out[0]) != len(grid[0]):
        return None
    return out


def _solve(grid: Grid) -> Grid:
    rows, cols = len(grid), len(grid[0])
    g = [row[:] for row in grid]
    bg = Counter(g[r][c] for r in range(rows) for c in range(cols)).most_common(1)[0][0]

    non_bg = {(r, c) for r in range(rows) for c in range(cols) if g[r][c] != bg}
    visited: set[Tuple[int, int]] = set()
    components: List[set[Tuple[int, int]]] = []
    for rc in non_bg:
        if rc in visited:
            continue
        comp: set[Tuple[int, int]] = set()
        q: deque[Tuple[int, int]] = deque([rc])
        while q:
            cr, cc = q.popleft()
            if (cr, cc) in visited:
                continue
            visited.add((cr, cc))
            comp.add((cr, cc))
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = cr + dr, cc + dc
                    if (nr, nc) in non_bg and (nr, nc) not in visited:
                        q.append((nr, nc))
        components.append(comp)

    distance = 5
    dot_map: Dict[Tuple[int, int], int] = {}
    for comp in components:
        if len(comp) != 3:
            continue
        min_r = min(r for r, _ in comp)
        max_r = max(r for r, _ in comp)
        min_c = min(c for _, c in comp)
        max_c = max(c for _, c in comp)
        h = max_r - min_r + 1
        w = max_c - min_c + 1
        norm = frozenset((r - min_r, c - min_c) for r, c in comp)
        tip_r = tip_c = None
        dr = dc = 0

        if h == 2 and w == 2:
            all_corners = {(0, 0), (0, 1), (1, 0), (1, 1)}
            missing = all_corners - set(norm)
            if len(missing) == 1:
                mr, mc = missing.pop()
                tip_r = min_r + (1 - mr)
                tip_c = min_c + (1 - mc)
                dr = -1 if mr == 1 else 1
                dc = -1 if mc == 1 else 1
        elif h == 2 and w == 3:
            if norm == frozenset([(0, 1), (1, 0), (1, 2)]):
                tip_r, tip_c = min_r, min_c + 1
                dr, dc = -1, 0
            elif norm == frozenset([(0, 0), (0, 2), (1, 1)]):
                tip_r, tip_c = max_r, min_c + 1
                dr, dc = 1, 0
        elif h == 3 and w == 2:
            if norm == frozenset([(0, 0), (1, 1), (2, 0)]):
                tip_r, tip_c = min_r + 1, max_c
                dr, dc = 0, 1
            elif norm == frozenset([(0, 1), (1, 0), (2, 1)]):
                tip_r, tip_c = min_r + 1, min_c
                dr, dc = 0, -1

        if tip_r is not None:
            dot_r = tip_r + distance * dr
            dot_c = tip_c + distance * dc
            if 0 <= dot_r < rows and 0 <= dot_c < cols:
                dot_map[(dot_r, dot_c)] = dot_map.get((dot_r, dot_c), 0) + 1

    cell_to_comp = {rc: i for i, comp in enumerate(components) for rc in comp}
    for (dot_r, dot_c), count in dot_map.items():
        if count > 1:
            g[dot_r][dot_c] = 1
        elif g[dot_r][dot_c] == bg:
            g[dot_r][dot_c] = 9
        else:
            ci = cell_to_comp.get((dot_r, dot_c))
            if ci is not None:
                for r, c in components[ci]:
                    g[r][c] = 9
    return g


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("triomino_tip_ray", triomino_tip_ray)]


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
            "engine": "s3_triomino_tip_ray",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_triomino_tip_ray",
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
    "solve_task",
    "submission_fragment",
    "train_replay",
    "triomino_tip_ray",
]
