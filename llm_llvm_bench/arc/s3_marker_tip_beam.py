"""S3 marker tip-beam language game (FoT).

Grammar family owned here:
  marker_tip_beam (canonical: eval task 3dc255db)
    S1: same canvas; background = 0; 8-connected multi-color objects.
    S2: majority color = shape; minority = marker cells.
    S3: tip = extreme edge favoring thin tip / thick adjacent / long beam.
    S4: remove markers; paint marker_color beam of length n_markers from tip.
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 3dc255db). Never submits to Kaggle.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def marker_tip_beam(grid: Grid) -> Optional[Grid]:
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
    visited = [[False] * cols for _ in range(rows)]
    components: List[List[Tuple[int, int, int]]] = []

    for r in range(rows):
        for c in range(cols):
            if g[r][c] != 0 and not visited[r][c]:
                comp: List[Tuple[int, int, int]] = []
                queue: deque[Tuple[int, int]] = deque([(r, c)])
                visited[r][c] = True
                while queue:
                    cr, cc = queue.popleft()
                    comp.append((cr, cc, g[cr][cc]))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = cr + dr, cc + dc
                            if (
                                0 <= nr < rows
                                and 0 <= nc < cols
                                and not visited[nr][nc]
                                and g[nr][nc] != 0
                            ):
                                visited[nr][nc] = True
                                queue.append((nr, nc))
                components.append(comp)

    for comp in components:
        color_counts = Counter(v for _, _, v in comp)
        if len(color_counts) < 2:
            continue
        sorted_colors = color_counts.most_common()
        shape_color = sorted_colors[0][0]
        marker_color = sorted_colors[-1][0]
        shape_cells = [(r, c) for r, c, v in comp if v == shape_color]
        marker_cells = [(r, c) for r, c, v in comp if v == marker_color]
        if not marker_cells or not shape_cells:
            continue

        n_markers = len(marker_cells)
        mc_r = sum(r for r, _ in marker_cells) / n_markers
        mc_c = sum(c for _, c in marker_cells) / n_markers
        min_r = min(r for r, _ in shape_cells)
        max_r = max(r for r, _ in shape_cells)
        min_c = min(c for _, c in shape_cells)
        max_c = max(c for _, c in shape_cells)

        candidates = [
            ("UP", [(r, c) for r, c in shape_cells if r == min_r]),
            ("DOWN", [(r, c) for r, c in shape_cells if r == max_r]),
            ("LEFT", [(r, c) for r, c in shape_cells if c == min_c]),
            ("RIGHT", [(r, c) for r, c in shape_cells if c == max_c]),
        ]
        adj_w = {
            "UP": sum(1 for r, c in shape_cells if r == min_r + 1),
            "DOWN": sum(1 for r, c in shape_cells if r == max_r - 1),
            "LEFT": sum(1 for r, c in shape_cells if c == min_c + 1),
            "RIGHT": sum(1 for r, c in shape_cells if c == max_c - 1),
        }
        dir_map = {
            "UP": (-1, 0),
            "DOWN": (1, 0),
            "LEFT": (0, -1),
            "RIGHT": (0, 1),
        }

        def tip_score(cand: Tuple[str, List[Tuple[int, int]]]):
            direction, cells = cand
            tip_cell = max(
                cells, key=lambda rc: (rc[0] - mc_r) ** 2 + (rc[1] - mc_c) ** 2
            )
            dr2, dc2 = dir_map[direction]
            avail = 0
            br, bc = tip_cell[0] + dr2, tip_cell[1] + dc2
            while 0 <= br < rows and 0 <= bc < cols and g[br][bc] == 0:
                avail += 1
                br += dr2
                bc += dc2
            beam_len = min(n_markers, avail)
            max_dist = max(
                ((r - mc_r) ** 2 + (c - mc_c) ** 2) ** 0.5 for r, c in cells
            )
            return (len(cells), -adj_w[direction], -beam_len, -max_dist)

        candidates.sort(key=tip_score)
        best_dir, best_cells = candidates[0]
        tip = max(
            best_cells, key=lambda rc: (rc[0] - mc_r) ** 2 + (rc[1] - mc_c) ** 2
        )
        dr, dc = dir_map[best_dir]
        for r, c in marker_cells:
            g[r][c] = 0
        beam_r, beam_c = tip[0] + dr, tip[1] + dc
        drawn = 0
        while 0 <= beam_r < rows and 0 <= beam_c < cols and drawn < n_markers:
            if g[beam_r][beam_c] != 0:
                break
            g[beam_r][beam_c] = marker_color
            drawn += 1
            beam_r += dr
            beam_c += dc
    return g


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("marker_tip_beam", marker_tip_beam)]


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
            "engine": "s3_marker_tip_beam",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_marker_tip_beam",
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
    "marker_tip_beam",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
