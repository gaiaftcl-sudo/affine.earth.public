"""S1 legend-motif tally language game (FoT).

Grammar family owned here:
  legend_motif_tally (canonical: eval task 58490d8a)
    S1: majority color is main-canvas background; a zero-panel is the legend.
    S2: legend markers are unique nonzero colors on that zero crop.
    S3: for each marker color, count 8-connected components in the main canvas
        (legend bbox masked to background).
    S4: output = legend-shaped zero grid; on each marker row, place `count`
        copies of the color at marker_col + 2k.
    C4: exact tally crop; licensed only when every training pair replays.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_MIN_LEGEND_CELLS = 9
_MIN_ZERO_FRAC = 0.55
_MAX_MARKERS = 10


def _majority(grid: Grid) -> int:
    return Counter(cell for row in grid for cell in row).most_common(1)[0][0]


def _comps8_count(grid: Grid, color: int) -> int:
    height = len(grid)
    width = len(grid[0])
    seen = [[False] * width for _ in range(height)]
    count = 0
    deltas = [
        (dr, dc)
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if not (dr == 0 and dc == 0)
    ]
    for r in range(height):
        for c in range(width):
            if seen[r][c] or grid[r][c] != color:
                continue
            count += 1
            queue = deque([(r, c)])
            seen[r][c] = True
            while queue:
                y, x = queue.popleft()
                for dy, dx in deltas:
                    ny, nx = y + dy, x + dx
                    if (
                        0 <= ny < height
                        and 0 <= nx < width
                        and not seen[ny][nx]
                        and grid[ny][nx] == color
                    ):
                        seen[ny][nx] = True
                        queue.append((ny, nx))
    return count


def _find_legend(
    grid: Grid, bg: int
) -> Optional[Tuple[int, int, int, int, List[Tuple[int, int, int]]]]:
    height = len(grid)
    width = len(grid[0])
    seen = [[False] * width for _ in range(height)]
    best: Optional[Tuple[Tuple[int, int, int], int, int, int, int, List[Tuple[int, int, int]]]] = None
    for r in range(height):
        for c in range(width):
            if grid[r][c] != 0 or seen[r][c]:
                continue
            queue = deque([(r, c)])
            seen[r][c] = True
            cells: List[Tuple[int, int]] = []
            while queue:
                y, x = queue.popleft()
                cells.append((y, x))
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if (
                        0 <= ny < height
                        and 0 <= nx < width
                        and not seen[ny][nx]
                        and grid[ny][nx] == 0
                    ):
                        seen[ny][nx] = True
                        queue.append((ny, nx))
            rows = [y for y, _ in cells]
            cols = [x for _, x in cells]
            r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
            crop_h, crop_w = r1 - r0 + 1, c1 - c0 + 1
            area = crop_h * crop_w
            if area < _MIN_LEGEND_CELLS:
                continue
            zeros = sum(
                1
                for y in range(r0, r1 + 1)
                for x in range(c0, c1 + 1)
                if grid[y][x] == 0
            )
            if zeros / area < _MIN_ZERO_FRAC:
                continue
            markers: List[Tuple[int, int, int]] = []
            for y in range(r0, r1 + 1):
                for x in range(c0, c1 + 1):
                    value = grid[y][x]
                    if value != 0:
                        markers.append((y - r0, x - c0, value))
            if not (1 <= len(markers) <= _MAX_MARKERS):
                continue
            colors = [color for _, _, color in markers]
            if len(colors) != len(set(colors)):
                continue
            if any(color == bg for color in colors):
                continue
            score = (zeros, len(cells), -len(markers))
            if best is None or score > best[0]:
                best = (score, r0, r1, c0, c1, markers)
    if best is None:
        return None
    _, r0, r1, c0, c1, markers = best
    return r0, r1, c0, c1, markers


def legend_motif_tally(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    bg = _majority(grid)
    legend = _find_legend(grid, bg)
    if legend is None:
        return None
    r0, r1, c0, c1, markers = legend
    height, width = r1 - r0 + 1, c1 - c0 + 1
    main = [row[:] for row in grid]
    for y in range(r0, r1 + 1):
        for x in range(c0, c1 + 1):
            main[y][x] = bg
    out = [[0] * width for _ in range(height)]
    for marker_r, marker_c, color in markers:
        count = _comps8_count(main, color)
        if count < 1:
            return None
        for index in range(count):
            col = marker_c + 2 * index
            if col >= width:
                return None
            out[marker_r][col] = color
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("legend_motif_tally", legend_motif_tally)]


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
            "engine": "s1_legend_motif_tally",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_legend_motif_tally",
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
    "legend_motif_tally",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
