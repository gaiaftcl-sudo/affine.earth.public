"""S2 color gate rewrite language game (FoT).

Grammar family owned here:
  color_gate_rewrite (canonical: eval task 9aaea919)
    S2 color-gate palette rewrite from public solver.
    C4: licensed only on perfect train replay.

Core transform adapted from public train+test-exact solver
(cristianoc/arc-agi-2-abstraction-dataset). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from collections import Counter
from typing import Any, Callable, Dict, Iterable, List, Tuple


Grid = List[List[int]]
ColumnIndex = int


def _get_background(grid: Grid) -> int:
    flat = [cell for row in grid for cell in row]
    return Counter(flat).most_common(1)[0][0]


def _find_cross_columns(grid: Grid) -> Dict[int, Dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    visited = [[False] * width for _ in range(height)]
    columns: Dict[int, Dict[str, Any]] = {}

    for r in range(height):
        for c in range(width):
            if visited[r][c]:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            visited[r][c] = True
            cells = []

            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < height and 0 <= ny < width and not visited[nx][ny] and grid[nx][ny] == color:
                        visited[nx][ny] = True
                        stack.append((nx, ny))

            if len(cells) != 11:
                continue

            rows = [x for x, _ in cells]
            cols = [y for _, y in cells]
            min_r, max_r = min(rows), max(rows)
            min_c, max_c = min(cols), max(cols)

            if max_r - min_r != 2 or max_c - min_c != 4:
                continue

            start_col = min_c
            pattern = [[grid[min_r + i][min_c + j] for j in range(5)] for i in range(3)]
            info = columns.setdefault(
                start_col,
                {
                    "rows": [],
                    "color": color,
                    "pattern": pattern,
                    "min_c": min_c,
                    "max_c": max_c,
                },
            )
            info["rows"].append(min_r)

    for info in columns.values():
        info["rows"].sort()

    return columns


def _instruction_segments(grid: Grid, background: int) -> List[Tuple[int, int, int]]:
    row = grid[-1]
    segments = []
    start = 0
    current = row[0]

    for idx, val in enumerate(row):
        if val != current:
            segments.append((current, start, idx - 1))
            start = idx
            current = val
    segments.append((current, start, len(row) - 1))

    return [seg for seg in segments if seg[0] != background]


def _map_segments_to_columns(
    segments: List[Tuple[int, int, int]],
    columns: Dict[int, Dict[str, Any]],
) -> Dict[int, List[int]]:
    if not columns:
        return {}

    mapping: Dict[int, List[int]] = {}
    for color, start, end in segments:
        center = (start + end) // 2
        matched = None
        for col_start, info in columns.items():
            if info["min_c"] <= center <= info["max_c"]:
                matched = col_start
                break
        if matched is None:
            matched = min(
                columns.keys(),
                key=lambda c: abs(((columns[c]["min_c"] + columns[c]["max_c"]) // 2) - center),
            )
        mapping.setdefault(matched, []).append(color)

    return mapping


def _draw_pattern(grid: Grid, top: int, left: int, pattern: List[List[int]]) -> None:
    for dr, row in enumerate(pattern):
        target = grid[top + dr]
        for dc, val in enumerate(row):
            target[left + dc] = val


def _recolor_column(grid: Grid, info: Dict[str, Any], background: int, new_color: int) -> None:
    original_color = info["color"]
    pattern = info["pattern"]
    recolored = [
        [new_color if cell == original_color else background if cell == background else cell for cell in row]
        for row in pattern
    ]

    for top in info["rows"]:
        _draw_pattern(grid, top, info["min_c"], recolored)

    info["pattern"] = recolored
    info["color"] = new_color


def _extend_column(grid: Grid, info: Dict[str, Any], count: int) -> None:
    if count <= 0:
        return

    step = 4  # 3 rows of the plus and one row gap
    top = min(info["rows"])
    pattern = info["pattern"]

    added = 0
    while added < count:
        new_top = top - step * (added + 1)
        if new_top < 0:
            break
        _draw_pattern(grid, new_top, info["min_c"], pattern)
        added += 1


def _clear_instruction_segments(grid: Grid, segments: List[Tuple[int, int, int]], background: int) -> Grid:
    """Return a copy of grid with the bottom-row instruction segments cleared to background."""
    out = [row[:] for row in grid]
    for _, start, end in segments:
        for c in range(start, end + 1):
            out[-1][c] = background
    return out


def _build_assignments(
    mapping: Dict[int, List[int]],
    columns: Dict[int, Dict[str, Any]],
) -> Dict[int, Dict[str, int]]:
    """Build per-column instruction: recolor flag and extend count.

    - recolor: 1 if colour 2 is present for the column, else 0
    - extend: number of extra stacks to add if colour 3 is present; this equals
      the total number of existing crosses across all columns flagged with colour 2.
    """
    color2_columns = [col for col, colors in mapping.items() if 2 in colors]
    total_crosses = sum(len(columns[col]["rows"]) for col in color2_columns)

    assignments: Dict[int, Dict[str, int]] = {}
    for col, colors in mapping.items():
        recolor_flag = 1 if 2 in colors else 0
        extend_count = total_crosses if 3 in colors else 0
        assignments[col] = {"recolor": recolor_flag, "extend": extend_count}
    return assignments


def fold_repaint(
    canvas: Grid, items: Iterable[Any], update: Callable[[Grid, Any], Grid]
) -> Grid:
    """Functional fold over items to repaint the canvas."""
    g = canvas
    for x in items:
        g = update(g, x)
    return g


# Public DSL-named wrappers to align with abstractions.md

def extractCrossColumns(grid: Grid) -> Dict[int, Dict[str, Any]]:
    return _find_cross_columns(grid)


def getBackground(grid: Grid) -> int:
    return _get_background(grid)


def readInstructionSegments(grid: Grid) -> List[Tuple[int, int, int]]:
    return _instruction_segments(grid, getBackground(grid))


def mapInstructionsToColumns(
    segments: List[Tuple[int, int, int]],
    columns: Dict[int, Dict[str, Any]],
) -> Dict[int, Dict[str, int]]:
    color_mapping = _map_segments_to_columns(segments, columns)
    return _build_assignments(color_mapping, columns)


def repaintColumn(canvas: Grid, column_info: Dict[str, Any], instruction: Dict[str, int]) -> Grid:
    out = [row[:] for row in canvas]
    bg = getBackground(canvas)
    if instruction.get("recolor", 0):
        _recolor_column(out, column_info, bg, 5)
    if instruction.get("extend", 0):
        _extend_column(out, column_info, instruction["extend"])
    return out


def clearInstructionSegments(
    canvas: Grid, segments: List[Tuple[int, int, int]], background: int
) -> Grid:
    return _clear_instruction_segments(canvas, segments, background)


def solve_9aaea919(grid: Grid) -> Grid:
    columns = extractCrossColumns(grid)
    segments = readInstructionSegments(grid)
    assignments = mapInstructionsToColumns(segments, columns)

    def repaint(canvas: Grid, column_index: ColumnIndex) -> Grid:
        instruction = assignments[column_index]
        column_info = columns[column_index]
        return repaintColumn(canvas, column_info, instruction)

    repainted = fold_repaint(grid, list(assignments.keys()), repaint)
    background = getBackground(grid)
    return clearInstructionSegments(repainted, segments, background)


def color_gate_rewrite(grid: Grid) -> Grid:
    return solve_9aaea919(grid)


def named_candidates():
    return [("color_gate_rewrite", color_gate_rewrite)]


def exact_candidates(train):
    matched = []
    for name, transform in named_candidates():
        try:
            if all(transform(example["input"]) == example["output"] for example in train):
                matched.append((name, transform))
        except Exception:
            continue
    return matched


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    train = task.get("train", [])
    exact = exact_candidates(train)
    if not exact:
        return {
            "engine": "s2_color_gate_rewrite",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_color_gate_rewrite",
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
    "color_gate_rewrite",
    "exact_candidates",
    "named_candidates",
    "solve_9aaea919",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
