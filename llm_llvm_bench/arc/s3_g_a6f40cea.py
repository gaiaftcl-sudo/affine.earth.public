"""Batch FoT engine for eval task a6f40cea.

Grammar family owned here:
  g_a6f40cea (canonical: eval task a6f40cea)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · a6f40cea). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_a6f40cea(grid: Grid) -> Optional[Grid]:
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
ARC-AGI Solver for task a6f40cea

Pattern: The input contains several rectangular outlines on a uniform background.
One rectangle uses color 3 as its border - this is the "main" rectangle.
Other rectangles (single-color or alternating-color borders) partially overlap with
the 3-rectangle. The output is the interior of the 3-rectangle, with the portions
of the other rectangles' borders that fall inside the interior made visible.
"""

from collections import Counter
from typing import List


def solve(grid: List[List[int]]) -> List[List[int]]:
    R, C = len(grid), len(grid[0])
    bg = Counter(v for row in grid for v in row).most_common(1)[0][0]

    # Find 3-cells and identify the main 3-rectangle (largest rectangular border)
    cells_3 = [(r, c) for r in range(R) for c in range(C) if grid[r][c] == 3]
    main_rect = _find_main_3_rect(cells_3)
    r3_rmin, r3_cmin, r3_rmax, r3_cmax = main_rect

    # Interior bounds and fill color
    ir1, ir2 = r3_rmin + 1, r3_rmax - 1
    ic1, ic2 = r3_cmin + 1, r3_cmax - 1
    fill = grid[ir1][ic1]

    # Initialize output with fill color
    orows, ocols = ir2 - ir1 + 1, ic2 - ic1 + 1
    result = [[fill] * ocols for _ in range(orows)]

    # Find other colored cells (not bg, not 3, not fill)
    color_cells = {}
    for r in range(R):
        for c in range(C):
            v = grid[r][c]
            if v != bg and v != 3 and v != fill:
                color_cells.setdefault(v, []).append((r, c))

    # Group colors by shared bounding box (alternating-color borders)
    color_bboxes = {}
    for v, cells in color_cells.items():
        bbox = (
            min(r for r, c in cells), min(c for r, c in cells),
            max(r for r, c in cells), max(c for r, c in cells),
        )
        color_bboxes[v] = bbox

    bbox_groups: dict[tuple, list] = {}
    for v, bbox in color_bboxes.items():
        bbox_groups.setdefault(bbox, []).append(v)

    # Project each rectangle's border into the 3-interior
    for bbox, colors in bbox_groups.items():
        br1, bc1, br2, bc2 = bbox

        if len(colors) == 1:
            # Single-color border
            color = colors[0]
            for r in range(br1, br2 + 1):
                for c in range(bc1, bc2 + 1):
                    if (r == br1 or r == br2 or c == bc1 or c == bc2):
                        if ir1 <= r <= ir2 and ic1 <= c <= ic2:
                            result[r - ir1][c - ic1] = color
        else:
            # Alternating-color border (2 colors)
            c0, c1_col = colors[0], colors[1]

            # Find the internal corner (corner of the rect inside the 3-interior)
            rect_corners = [(br1, bc1), (br1, bc2), (br2, bc1), (br2, bc2)]
            internal_corner = None
            for rc, cc in rect_corners:
                if ir1 <= rc <= ir2 and ic1 <= cc <= ic2:
                    internal_corner = (rc, cc)
                    break

            if internal_corner is not None:
                cr, cc = internal_corner
                # Find nearest visible cell to the internal corner
                all_vis = []
                for v in colors:
                    all_vis.extend((r, c, v) for r, c in color_cells[v])
                all_vis.sort(key=lambda x: abs(x[0] - cr) + abs(x[1] - cc))
                corner_color = all_vis[0][2]
                other_col = c0 if corner_color == c1_col else c1_col

                for r in range(br1, br2 + 1):
                    for c in range(bc1, bc2 + 1):
                        if (r == br1 or r == br2 or c == bc1 or c == bc2):
                            if ir1 <= r <= ir2 and ic1 <= c <= ic2:
                                dist = abs(r - cr) + abs(c - cc)
                                val = corner_color if dist % 2 == 0 else other_col
                                result[r - ir1][c - ic1] = val
            else:
                # No internal corner - use standard checkerboard from visible cells
                sample = color_cells[c0][0]
                if (sample[0] + sample[1]) % 2 == 0:
                    even_color, odd_color = c0, c1_col
                else:
                    even_color, odd_color = c1_col, c0
                for r in range(br1, br2 + 1):
                    for c in range(bc1, bc2 + 1):
                        if (r == br1 or r == br2 or c == bc1 or c == bc2):
                            if ir1 <= r <= ir2 and ic1 <= c <= ic2:
                                val = even_color if (r + c) % 2 == 0 else odd_color
                                result[r - ir1][c - ic1] = val

    return result


def _find_main_3_rect(cells_3):
    """Find the largest rectangular border among 3-cells."""
    if not cells_3:
        return None
    cell_set = set(cells_3)

    # Try all possible TL corners and find matching rectangles
    best = None
    best_area = 0
    rows_with_3 = sorted(set(r for r, c in cells_3))
    cols_with_3 = sorted(set(c for r, c in cells_3))

    for r1 in rows_with_3:
        for r2 in rows_with_3:
            if r2 <= r1 + 1:
                continue
            for c1 in cols_with_3:
                for c2 in cols_with_3:
                    if c2 <= c1 + 1:
                        continue
                    # Check if (r1,c1)-(r2,c2) forms a valid 3-border rectangle
                    if not _is_rect_border(cell_set, r1, c1, r2, c2):
                        continue
                    area = (r2 - r1 - 1) * (c2 - c1 - 1)
                    if area > best_area:
                        best_area = area
                        best = (r1, c1, r2, c2)
    return best


def _is_rect_border(cell_set, r1, c1, r2, c2):
    """Check if the border of rectangle (r1,c1)-(r2,c2) is present in cell_set."""
    # Check top and bottom borders
    for c in range(c1, c2 + 1):
        if (r1, c) not in cell_set or (r2, c) not in cell_set:
            return False
    # Check left and right borders
    for r in range(r1, r2 + 1):
        if (r, c1) not in cell_set or (r, c2) not in cell_set:
            return False
    return True


if __name__ == "__main__":
    import json
    import sys

    with open("/Users/evanpieser/arc-puzzle-catalog/dataset/tasks/a6f40cea.json") as f:
        task = json.load(f)

    all_pass = True
    for i, ex in enumerate(task["train"]):
        result = solve(ex["input"])
        expected = ex["output"]
        match = result == expected
        print(f"Train {i}: {'PASS' if match else 'FAIL'}")
        if not match:
            for ri in range(len(expected)):
                if ri < len(result) and result[ri] != expected[ri]:
                    print(f"  Row {ri}: got {result[ri]}")
                    print(f"       exp {expected[ri]}")
            all_pass = False

    for i, ex in enumerate(task["test"]):
        result = solve(ex["input"])
        expected = ex["output"]
        match = result == expected
        print(f"Test {i}: {'PASS' if match else 'FAIL'}")
        if not match:
            for ri in range(len(expected)):
                if ri < len(result) and result[ri] != expected[ri]:
                    print(f"  Row {ri}: got {result[ri]}")
                    print(f"       exp {expected[ri]}")
            all_pass = False

    if all_pass:
        print("\nALL PASS")
    else:
        print("\nSOME FAILURES")
    sys.exit(0 if all_pass else 1)



def _solve(grid: Grid):
    return solve(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_a6f40cea", g_a6f40cea)]


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
            "engine": "s3_g_a6f40cea",
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
        "engine": "s3_g_a6f40cea",
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
    "g_a6f40cea",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
