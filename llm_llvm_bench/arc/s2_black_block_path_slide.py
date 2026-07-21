"""S2 black-block path slide language game (FoT).

Grammar family owned here:
  black_block_path_slide (canonical: eval task 332f06d7)
    S1: same canvas; border-majority color = background.
    S2: black (0) forms an N×N block; red (2) optional attractor.
    S3: path color = majority non-bg / non-0 / non-2 fill.
    S4: BFS over valid N×N placements on the path; slide black to
        farthest cell (nearest red TL if red present); refill vacated
        cells with path color.
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 332f06d7). Never submits to Kaggle.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def black_block_path_slide(grid: Grid) -> Optional[Grid]:
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

    border = (
        [grid[0][c] for c in range(cols)]
        + [grid[rows - 1][c] for c in range(cols)]
        + [grid[r][0] for r in range(rows)]
        + [grid[r][cols - 1] for r in range(rows)]
    )
    bg = Counter(border).most_common(1)[0][0]

    black_cells = [(r, c) for r in range(rows) for c in range(cols) if g[r][c] == 0]
    red_cells = [(r, c) for r in range(rows) for c in range(cols) if g[r][c] == 2]
    if not black_cells:
        raise ValueError("no black block")

    min_r = min(r for r, _ in black_cells)
    max_r = max(r for r, _ in black_cells)
    n = max_r - min_r + 1
    min_c = min(c for _, c in black_cells)
    start = (min_r, min_c)

    path_counts: Counter[int] = Counter()
    for r in range(rows):
        for c in range(cols):
            v = g[r][c]
            if v != bg and v != 0 and v != 2:
                path_counts[v] += 1
    if not path_counts:
        raise ValueError("no path color")
    path_color = path_counts.most_common(1)[0][0]

    def is_valid(r: int, c: int) -> bool:
        if r < 0 or r + n > rows or c < 0 or c + n > cols:
            return False
        for dr in range(n):
            for dc in range(n):
                if g[r + dr][c + dc] == bg:
                    return False
        return True

    visited: Dict[Tuple[int, int], int] = {start: 0}
    queue: deque[Tuple[Tuple[int, int], int]] = deque([(start, 0)])
    max_dist = 0
    while queue:
        (r, c), d = queue.popleft()
        if d > max_dist:
            max_dist = d
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if (nr, nc) not in visited and is_valid(nr, nc):
                visited[(nr, nc)] = d + 1
                queue.append(((nr, nc), d + 1))

    candidates = [pos for pos, d in visited.items() if d == max_dist]
    if not candidates:
        raise ValueError("no slide destination")
    if red_cells:
        red_tl = (min(r for r, _ in red_cells), min(c for _, c in red_cells))
        dest = min(
            candidates, key=lambda p: abs(p[0] - red_tl[0]) + abs(p[1] - red_tl[1])
        )
    else:
        dest = candidates[0]

    for r, c in black_cells:
        g[r][c] = path_color
    for dr in range(n):
        for dc in range(n):
            g[dest[0] + dr][dest[1] + dc] = 0
    return g


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("black_block_path_slide", black_block_path_slide)]


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
            "engine": "s2_black_block_path_slide",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_black_block_path_slide",
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
    "black_block_path_slide",
    "exact_candidates",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
