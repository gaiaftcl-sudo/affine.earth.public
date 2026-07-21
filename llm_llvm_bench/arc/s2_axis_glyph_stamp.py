"""S2 axis-glyph stamp language game (FoT).

Grammar family owned here:
  axis_glyph_stamp (canonical: eval task 247ef758)
    S1: same canvas shape.
    S2: solid nonzero axis column splits left glyphs from right room.
    S3: top-row colors mark stamp columns; right-col colors mark stamp rows.
    S4: each left glyph of color C stamps centered copies at all (row_C × col_C)
        marker pairs; source glyph cells clear to 0.
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(cristianoc/arc-agi-2-abstraction-dataset). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple



# Typed aliases for the DSL subset
Grid = List[List[int]]
Color = int
Row = int
Column = int
Glyph = List[Tuple[int, int, int]]  # list of (r, c, color) cells


def deep_copy(grid: Grid) -> Grid:
    return [row[:] for row in grid]


def fold_repaint(
    initial: Grid,
    items: List[Tuple[Color, Glyph]],
    update: Callable[[Grid, Tuple[Color, Glyph]], Grid],
) -> Grid:
    canvas = initial
    for item in items:
        canvas = update(canvas, item)
    return canvas


def findAxisColumn(grid: Grid) -> Optional[Column]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    for c in range(w):
        column = [grid[r][c] for r in range(h)]
        if column and column[0] != 0 and all(v == column[0] for v in column):
            return c
    return None


def extractGlyphs(grid: Grid, axis_col: Column) -> Dict[Color, Glyph]:
    acc: Dict[Color, Glyph] = {}
    # collect
    for r, row in enumerate(grid):
        for c in range(axis_col):
            val = row[c]
            if val != 0:
                acc.setdefault(val, []).append((r, c, val))
    # reorder by min-row descending to match solver semantics
    order = sorted(acc.keys(), key=lambda col: min(rcv[0] for rcv in acc[col]), reverse=True)
    return {col: acc[col] for col in order}


def extractColumnMarkers(grid: Grid, axis_col: Column) -> Dict[Color, List[Column]]:
    top = grid[0] if grid else []
    mapping: Dict[Color, List[Column]] = {}
    for c in range(axis_col + 1, len(top)):
        v = top[c]
        if v != 0:
            mapping.setdefault(v, []).append(c)
    for k in list(mapping.keys()):
        mapping[k] = sorted(mapping[k])
    return mapping


def extractRowMarkers(grid: Grid) -> Dict[Color, List[Row]]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    mapping: Dict[Color, List[Row]] = {}
    if w == 0:
        return mapping
    last = w - 1
    for r in range(h):
        v = grid[r][last]
        if v != 0:
            mapping.setdefault(v, []).append(r)
    for k in list(mapping.keys()):
        mapping[k] = sorted(mapping[k])
    return mapping


def glyphMinRow(glyph: Glyph) -> int:
    return min(r for r, _, _ in glyph) if glyph else 0


def placeGlyphs(canvas: Grid, glyph: Glyph, rows: List[Row], cols: List[Column]) -> Grid:
    if not glyph:
        return canvas
    h = len(canvas)
    w = len(canvas[0]) if h else 0
    # colour is stored within the glyph cells
    r0, c0, color = glyph[0]
    g = deep_copy(canvas)
    # clear source glyph cells
    for r, c, _ in glyph:
        if 0 <= r < h and 0 <= c < w:
            g[r][c] = 0
    # compute centre and offsets
    rows_list = [r for r, _, _ in glyph]
    cols_list = [c for _, c, _ in glyph]
    min_r, max_r = min(rows_list), max(rows_list)
    min_c, max_c = min(cols_list), max(cols_list)
    cr = (min_r + max_r) // 2
    cc = (min_c + max_c) // 2
    offsets = [(r - cr, c - cc) for r, c, _ in glyph]
    # stamp at every row/column combination
    for tr in rows:
        for tc in cols:
            for dr, dc in offsets:
                rr = tr + dr
                cc2 = tc + dc
                if 0 <= rr < h and 0 <= cc2 < w:
                    g[rr][cc2] = color
    return g


def solve_247ef758(grid: Grid) -> Grid:
    axis_col = findAxisColumn(grid)
    if axis_col is None:
        return grid

    glyphs = extractGlyphs(grid, axis_col)
    col_markers = extractColumnMarkers(grid, axis_col)
    row_markers = extractRowMarkers(grid)
    glyph_entries = list(glyphs.items())

    def place(canvas: Grid, entry: Tuple[Color, Glyph]) -> Grid:
        color, glyph = entry
        if color not in col_markers or color not in row_markers:
            return canvas
        return placeGlyphs(canvas, glyph, row_markers[color], col_markers[color])

    return fold_repaint(grid, glyph_entries, place)


def axis_glyph_stamp(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = solve_247ef758(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Any]]:
    _ = train
    return [("axis_glyph_stamp", axis_glyph_stamp)]


def exact_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Any]]:
    matched: List[Tuple[str, Any]] = []
    for name, transform in named_candidates(train):
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
            "engine": "s2_axis_glyph_stamp",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_axis_glyph_stamp",
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
    "axis_glyph_stamp",
    "exact_candidates",
    "named_candidates",
    "solve_247ef758",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
