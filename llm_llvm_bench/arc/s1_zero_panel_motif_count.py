"""S1 zero-panel motif-count projection language game (FoT).

Grammar family owned here:
  zero_panel_motif_count (canonical: eval task 58490d8a)
    S1: majority color = wall; output canvas = bbox of all 0-cells (zero panel).
    S2: panel markers = nonzero non-wall cells inside that bbox.
    S3: for each marker color C, count 8-connected components of C outside the panel;
        paint C on the marker row at columns marker_col + 2*k for k in 0..count-1.
    S4: remaining panel cells stay 0.
    C4: exact projected panel; licensed only when every training pair replays.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _majority(grid: Grid) -> int:
    return Counter(cell for row in grid for cell in row).most_common(1)[0][0]


def _zero_bbox(grid: Grid) -> Optional[Tuple[int, int, int, int]]:
    cells = [
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == 0
    ]
    if not cells:
        return None
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), max(rows), min(cols), max(cols)


def _count_motifs8(
    grid: Grid, color: int, exclude: Tuple[int, int, int, int]
) -> int:
    height, width = len(grid), len(grid[0])
    er0, er1, ec0, ec1 = exclude
    seen = [[False] * width for _ in range(height)]
    count = 0
    for r in range(height):
        for c in range(width):
            if grid[r][c] != color or seen[r][c]:
                continue
            if er0 <= r <= er1 and ec0 <= c <= ec1:
                continue
            count += 1
            queue = deque([(r, c)])
            seen[r][c] = True
            while queue:
                x, y = queue.popleft()
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if (
                            0 <= nx < height
                            and 0 <= ny < width
                            and not seen[nx][ny]
                            and grid[nx][ny] == color
                        ):
                            if er0 <= nx <= er1 and ec0 <= ny <= ec1:
                                continue
                            seen[nx][ny] = True
                            queue.append((nx, ny))
    return count


def zero_panel_motif_count(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    bg = _majority(grid)
    bbox = _zero_bbox(grid)
    if bbox is None:
        return None
    r0, r1, c0, c1 = bbox
    height, width = r1 - r0 + 1, c1 - c0 + 1
    if height < 2 or width < 2:
        return None
    out = [[0] * width for _ in range(height)]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            value = grid[r][c]
            if value in (0, bg):
                continue
            local_r, local_c = r - r0, c - c0
            count = _count_motifs8(grid, value, bbox)
            if count < 1:
                return None
            for k in range(count):
                col = local_c + 2 * k
                if 0 <= col < width:
                    out[local_r][col] = value
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("zero_panel_motif_count", zero_panel_motif_count)]


def exact_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    matched: List[Tuple[str, Transform]] = []
    for name, transform in named_candidates(train):
        if all(
            len(ex["input"]) > len(ex["output"])
            or len(ex["input"][0]) > len(ex["output"][0])
            for ex in train
        ) and all(transform(ex["input"]) == ex["output"] for ex in train):
            matched.append((name, transform))
    return matched


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    train = task.get("train", [])
    exact = exact_candidates(train)
    if not exact:
        return {
            "engine": "s1_zero_panel_motif_count",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_zero_panel_motif_count",
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
    "zero_panel_motif_count",
]
