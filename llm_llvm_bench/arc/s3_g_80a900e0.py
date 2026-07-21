"""Batch FoT engine for eval task 80a900e0.

Grammar family owned here:
  g_80a900e0 (canonical: eval task 80a900e0)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 80a900e0). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_80a900e0(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


from collections import defaultdict, deque


def solve(grid):
    R, C = len(grid), len(grid[0])

    bg_even = grid[0][0]
    bg_odd = grid[0][1]

    # Find all non-checkerboard cells
    non_bg = {}
    for r in range(R):
        for c in range(C):
            expected = bg_even if (r + c) % 2 == 0 else bg_odd
            if grid[r][c] != expected:
                non_bg[(r, c)] = grid[r][c]

    if not non_bg:
        return [row[:] for row in grid]

    # Separate into independent diamonds via diagonal connectivity
    visited = set()
    diamonds = []
    for cell in non_bg:
        if cell in visited:
            continue
        component = {}
        queue = deque([cell])
        visited.add(cell)
        while queue:
            r, c = queue.popleft()
            component[(r, c)] = non_bg[(r, c)]
            for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in non_bg and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        diamonds.append(component)

    output = [row[:] for row in grid]

    def find_lines(cells):
        cell_set = set(cells)
        vis = set()
        lines = []
        for cell in cells:
            if cell in vis:
                continue
            line = []
            q = deque([cell])
            vis.add(cell)
            while q:
                r, c = q.popleft()
                line.append((r, c))
                for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in cell_set and (nr, nc) not in vis:
                        vis.add((nr, nc))
                        q.append((nr, nc))
            lines.append(sorted(line))
        return lines

    for diamond in diamonds:
        # Interior color = most common within this diamond
        color_counts = defaultdict(int)
        for color in diamond.values():
            color_counts[color] += 1
        interior_color = max(color_counts, key=color_counts.get)

        # Edge cells grouped by non-interior color
        color_groups = defaultdict(list)
        for (r, c), color in diamond.items():
            if color != interior_color:
                color_groups[color].append((r, c))

        # Diamond center
        center_r = sum(r for r, c in diamond) / len(diamond)
        center_c = sum(c for r, c in diamond) / len(diamond)

        for color, cells in color_groups.items():
            lines = find_lines(cells)

            for line in lines:
                if len(line) < 2:
                    r0, c0 = line[0]
                    dr = 1 if r0 > center_r else -1
                    dc = 1 if c0 > center_c else -1
                    r, c = r0, c0
                    while True:
                        r += dr
                        c += dc
                        if 0 <= r < R and 0 <= c < C:
                            output[r][c] = color
                        else:
                            break
                    continue

                dr = line[1][0] - line[0][0]
                dc = line[1][1] - line[0][1]
                edge_dir = (1 if dr >= 0 else -1, 1 if dc >= 0 else -1)

                mid_r = sum(r for r, c in line) / len(line)
                mid_c = sum(c for r, c in line) / len(line)

                perp1 = (-edge_dir[1], edge_dir[0])
                perp2 = (edge_dir[1], -edge_dir[0])

                toward_r = mid_r - center_r
                toward_c = mid_c - center_c
                dot1 = perp1[0] * toward_r + perp1[1] * toward_c
                dot2 = perp2[0] * toward_r + perp2[1] * toward_c
                outward = perp1 if dot1 > dot2 else perp2

                for endpoint in [line[0], line[-1]]:
                    r, c = endpoint
                    while True:
                        r += outward[0]
                        c += outward[1]
                        if 0 <= r < R and 0 <= c < C:
                            output[r][c] = color
                        else:
                            break

    return output



def _solve(grid: Grid):
    return solve(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_80a900e0", g_80a900e0)]


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
            "engine": "s3_g_80a900e0",
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
        "engine": "s3_g_80a900e0",
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
    "g_80a900e0",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
