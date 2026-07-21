"""Batch FoT engine for eval task cb2d8a2c.

Grammar family owned here:
  g_cb2d8a2c (canonical: eval task cb2d8a2c)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · cb2d8a2c). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_cb2d8a2c(grid: Grid) -> Optional[Grid]:
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
ARC-AGI puzzle cb2d8a2c solver.

Pattern: A single 3-marker and multiple line segments (1s and 2s).
- All 1s become 2s in output.
- A continuous frame of 3s is drawn from the marker, zigzagging around each segment.
- For each segment, the number of 1s determines the offset (num_1s + 1).
- The 1s indicate the "open" end; the frame wraps on the opposite side.
- The frame extends perpendicular to the segment by offset, and the turn-row/col
  between marker and each segment is at (segment_pos - offset) toward the marker.
"""
from copy import deepcopy


def transform(grid):
    result = [row[:] for row in grid]
    rows, cols = len(grid), len(grid[0])

    # Find marker (3)
    marker = None
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 3:
                marker = (r, c)
                break
        if marker:
            break
    mr, mc = marker

    # Find segments via BFS on 1/2 cells
    visited = [[False] * cols for _ in range(rows)]
    segments = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] in (1, 2) and not visited[r][c]:
                comp = []
                stack = [(r, c)]
                visited[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    comp.append((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc] and grid[nr][nc] in (1, 2):
                            visited[nr][nc] = True
                            stack.append((nr, nc))
                if len(comp) < 2:
                    continue
                row_set = set(cr for cr, _ in comp)
                col_set = set(cc for _, cc in comp)
                if len(row_set) == 1:
                    segments.append(('h', min(row_set), min(col_set), max(col_set)))
                elif len(col_set) == 1:
                    segments.append(('v', min(col_set), min(row_set), max(row_set)))

    # Determine orientation
    h_segs = [s for s in segments if s[0] == 'h']
    v_segs = [s for s in segments if s[0] == 'v']
    orientation = 'h' if len(h_segs) >= len(v_segs) else 'v'
    segs = h_segs if orientation == 'h' else v_segs

    # Compute per-segment frame data
    seg_data = []
    if orientation == 'h':
        for _, seg_row, seg_left, seg_right in segs:
            ones = [c for c in range(seg_left, seg_right + 1) if grid[seg_row][c] == 1]
            off = len(ones) + 1
            ones_avg = sum(ones) / len(ones)
            mid = (seg_left + seg_right) / 2
            # Frame wraps opposite to where the 1s are concentrated
            if ones_avg >= mid:
                turn_col = seg_left - off      # 1s at right → wrap LEFT
            else:
                turn_col = seg_right + off     # 1s at left → wrap RIGHT
            # Turn row toward the marker
            turn_row = seg_row - off if mr < seg_row else seg_row + off
            seg_data.append({'pos': seg_row, 'tc': turn_col, 'tr': turn_row})
        seg_data.sort(key=lambda s: abs(s['pos'] - mr))
        edge = rows - 1 if mr < min(s['pos'] for s in seg_data) else 0
    else:
        for _, seg_col, seg_top, seg_bot in segs:
            ones = [r for r in range(seg_top, seg_bot + 1) if grid[r][seg_col] == 1]
            off = len(ones) + 1
            ones_avg = sum(ones) / len(ones)
            mid = (seg_top + seg_bot) / 2
            if ones_avg >= mid:
                turn_row = seg_top - off       # 1s at bottom → wrap TOP
            else:
                turn_row = seg_bot + off       # 1s at top → wrap BOTTOM
            # Turn col toward the marker
            turn_col = seg_col - off if mc < seg_col else seg_col + off
            seg_data.append({'pos': seg_col, 'tc': turn_col, 'tr': turn_row})
        seg_data.sort(key=lambda s: abs(s['pos'] - mc))
        edge = cols - 1 if mc < min(s['pos'] for s in seg_data) else 0

    # Draw line helper (only overwrites background=8 cells)
    def draw(r1, c1, r2, c2):
        if r1 == r2:
            for c in range(min(c1, c2), max(c1, c2) + 1):
                if 0 <= c < cols and result[r1][c] == 8:
                    result[r1][c] = 3
        elif c1 == c2:
            for r in range(min(r1, r2), max(r1, r2) + 1):
                if 0 <= r < rows and result[r][c1] == 8:
                    result[r][c1] = 3

    # Draw frame path
    r, c = mr, mc
    if orientation == 'h':
        for s in seg_data:
            draw(r, c, s['tr'], c); r = s['tr']
            draw(r, c, r, s['tc']); c = s['tc']
        draw(r, c, edge, c)
    else:
        for s in seg_data:
            draw(r, c, r, s['tc']); c = s['tc']
            draw(r, c, s['tr'], c); r = s['tr']
        draw(r, c, r, edge)

    # Convert all 1s to 2s
    for r in range(rows):
        for c in range(cols):
            if result[r][c] == 1:
                result[r][c] = 2

    return result



def _solve(grid: Grid):
    return transform(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_cb2d8a2c", g_cb2d8a2c)]


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
            "engine": "s3_g_cb2d8a2c",
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
        "engine": "s3_g_cb2d8a2c",
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
    "g_cb2d8a2c",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
