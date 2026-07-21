"""S1 topology schematic language game (FoT).

Grammar family owned here:
  topology_schematic (canonical: eval task 2d0172a1)
    S1: majority color = background; minority = foreground structure.
    S2: 4-connected fg components form a containment tree (path to border
        must cross parent). Loops enclose; leaves do not.
    S3: lossy schematic — ignore exact shapes; draw nested frames from the
        tree with leaf markers as checker rows / bay notches; place children
        by centroid side (L/R/U/D) relative to the medium sub-loop.
    S4: root-level outside leaves attach as a 3-cell exterior bar on their
        dominant side of the main loop.
    C4: exact schematic grid; licensed only when every training pair replays.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]
Side = str  # "LEFT" | "RIGHT" | "ABOVE" | "BELOW"


def _majority(grid: Grid) -> int:
    return Counter(value for row in grid for value in row).most_common(1)[0][0]


def _fg_bg(grid: Grid) -> Tuple[int, int]:
    bg = _majority(grid)
    colors = {value for row in grid for value in row}
    others = [color for color in colors if color != bg]
    if len(others) != 1:
        return bg, bg
    return others[0], bg


def _components(grid: Grid, color: int) -> List[List[Cell]]:
    height = len(grid)
    width = len(grid[0])
    seen = [[False] * width for _ in range(height)]
    out: List[List[Cell]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or seen[row][col]:
                continue
            queue: deque[Cell] = deque([(row, col)])
            seen[row][col] = True
            cells: List[Cell] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))
            out.append(cells)
    return out


def _centroid(cells: Sequence[Cell]) -> Tuple[float, float]:
    return (
        sum(r for r, _ in cells) / len(cells),
        sum(c for _, c in cells) / len(cells),
    )


def _bbox(cells: Sequence[Cell]) -> Tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), max(rows), min(cols), max(cols)


def _is_loop(grid: Grid, comp: Sequence[Cell]) -> bool:
    height = len(grid)
    width = len(grid[0])
    loop: Set[Cell] = set(comp)
    exterior: Set[Cell] = set()
    queue: deque[Cell] = deque()
    for row in range(height):
        for col in range(width):
            if (row in (0, height - 1) or col in (0, width - 1)) and (
                row,
                col,
            ) not in loop:
                exterior.add((row, col))
                queue.append((row, col))
    while queue:
        r, c = queue.popleft()
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if (
                0 <= nr < height
                and 0 <= nc < width
                and (nr, nc) not in exterior
                and (nr, nc) not in loop
            ):
                exterior.add((nr, nc))
                queue.append((nr, nc))
    for row in range(height):
        for col in range(width):
            if (row, col) not in loop and (row, col) not in exterior:
                return True
    return False


def _containment_parent(grid: Grid, components: Sequence[Sequence[Cell]]) -> List[Optional[int]]:
    height = len(grid)
    width = len(grid[0])
    parent: List[Optional[int]] = [None] * len(components)
    for index, comp in enumerate(components):
        candidates: List[int] = []
        for other_index, other in enumerate(components):
            if index == other_index:
                continue
            loop = set(other)
            reach = False
            seen: Set[Cell] = set(comp)
            queue: deque[Cell] = deque(comp)
            while queue:
                r, c = queue.popleft()
                if r == 0 or c == 0 or r == height - 1 or c == width - 1:
                    reach = True
                    break
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and (nr, nc) not in loop
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            if not reach:
                candidates.append(other_index)
        if candidates:
            parent[index] = min(candidates, key=lambda j: len(components[j]))
    return parent


def _dominant_side(dr: float, dc: float) -> Side:
    if abs(dr) >= abs(dc):
        return "BELOW" if dr > 0 else "ABOVE"
    return "RIGHT" if dc > 0 else "LEFT"


def _outside_side(
    cells: Sequence[Cell], main: Sequence[Cell]
) -> Side:
    cy, cx = _centroid(cells)
    r0, r1, c0, c1 = _bbox(main)
    if cy < r0:
        return "ABOVE"
    if cy > r1:
        return "BELOW"
    if cx < c0:
        return "LEFT"
    if cx > c1:
        return "RIGHT"
    mcy, mcx = _centroid(main)
    return _dominant_side(cy - mcy, cx - mcx)


def _render_leaves_only(n_leaves: int, fg: int, bg: int) -> Grid:
    height = 2 * n_leaves + 3
    width = 5
    grid = [[bg] * width for _ in range(height)]
    for col in range(width):
        grid[0][col] = fg
        grid[height - 1][col] = fg
    for row in range(height):
        grid[row][0] = fg
        grid[row][width - 1] = fg
    for leaf in range(n_leaves):
        row = 2 + 2 * leaf
        for col in range(1, width - 1):
            grid[row][col] = fg if col % 2 == 0 else bg
    return grid


def _paint_border(grid: Grid, r0: int, r1: int, c0: int, c1: int, fg: int) -> None:
    for col in range(c0, c1 + 1):
        grid[r0][col] = fg
        grid[r1][col] = fg
    for row in range(r0, r1 + 1):
        grid[row][c0] = fg
        grid[row][c1] = fg


def _paint_checker_row(grid: Grid, row: int, c0: int, c1: int, fg: int, bg: int) -> None:
    for col in range(c0, c1 + 1):
        grid[row][col] = fg if col % 2 == 0 else bg


def _render_with_medium(
    n_inner: int,
    leaf_sides: Set[Side],
    outside_sides: Set[Side],
    fg: int,
    bg: int,
) -> Optional[Grid]:
    if n_inner < 1:
        return None
    inner_w = 2 * n_inner + 3
    left_bay = 3 if "LEFT" in leaf_sides else 1
    right_bay = 3 if "RIGHT" in leaf_sides else 1
    # When a below-leaf is present without a right-leaf, keep a 1-col gap
    # before the right wall (observed on 2d0172a1 train0).
    if "BELOW" in leaf_sides and "RIGHT" not in leaf_sides:
        right_bay = 1
    above = 2 if "ABOVE" in leaf_sides else 0
    below = 2 if "BELOW" in leaf_sides else 0
    # Base med frame content height is 9 (= 1 top + 1 pad + 5 inner + 1 pad + 1 bot).
    # above/below insert 2-row marker bands inside the outer frame.
    frame_h = 9 + above + below
    frame_w = 1 + left_bay + inner_w + right_bay + 1

    ext_left = 3 if "LEFT" in outside_sides else 0
    ext_right = 3 if "RIGHT" in outside_sides else 0
    ext_above = 3 if "ABOVE" in outside_sides else 0
    ext_below = 3 if "BELOW" in outside_sides else 0

    # Outside RIGHT replaces an internal right bay when both would apply
    # (train0: exterior cols, no internal 3-bay).
    if ext_right and "RIGHT" not in leaf_sides:
        pass
    elif ext_right and "RIGHT" in leaf_sides:
        # not observed; keep both
        pass

    height = ext_above + frame_h + ext_below
    width = ext_left + frame_w + ext_right
    grid = [[bg] * width for _ in range(height)]

    fr0 = ext_above
    fr1 = ext_above + frame_h - 1
    fc0 = ext_left
    fc1 = ext_left + frame_w - 1
    _paint_border(grid, fr0, fr1, fc0, fc1, fg)

    # Inner frame vertical placement inside the outer frame.
    # Standard (no above/below): inner at relative rows 2..6.
    # With above band: shift inner down by `above`.
    # With below band: inner stays, marker sits after lower pad.
    inner_r0 = fr0 + 2 + above
    inner_r1 = inner_r0 + 4
    inner_c0 = fc0 + 1 + left_bay
    inner_c1 = inner_c0 + inner_w - 1
    _paint_border(grid, inner_r0, inner_r1, inner_c0, inner_c1, fg)

    checker_row = inner_r0 + 2
    _paint_checker_row(grid, checker_row, fc0 + 1, fc1 - 1 + ext_right, fg, bg)
    # Checker may extend into right exterior; keep outer/inner verticals fg.
    grid[checker_row][fc0] = fg
    grid[checker_row][fc1] = fg
    grid[checker_row][inner_c0] = fg
    grid[checker_row][inner_c1] = fg

    inner_mid_c = inner_c0 + inner_w // 2

    if "ABOVE" in leaf_sides:
        # Marker on the upper band, aligned to the inner-frame midline.
        grid[fr0 + 2][inner_mid_c] = fg

    if "BELOW" in leaf_sides:
        # Marker on the lower band, center of the inner frame (tr0: col 4).
        marker_row = inner_r1 + 2
        grid[marker_row][inner_mid_c] = fg

    if ext_below:
        # 3-row bar: all bg with one fg marker on the middle row at inner mid.
        grid[fr1 + 2][inner_mid_c] = fg

    if ext_above:
        grid[1][inner_mid_c] = fg

    if ext_left:
        mid_r = (fr0 + fr1) // 2
        if grid[mid_r][1] == bg:
            grid[mid_r][1] = fg

    return grid


def topology_schematic(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    fg, bg = _fg_bg(grid)
    if fg == bg:
        return None
    comps = sorted(_components(grid, fg), key=len, reverse=True)
    if not comps:
        return None
    loops = [_is_loop(grid, comp) for comp in comps]
    if not loops[0]:
        return None
    parent = _containment_parent(grid, comps)
    children: Dict[int, List[int]] = {index: [] for index in range(len(comps))}
    roots: List[int] = []
    for index, par in enumerate(parent):
        if par is None:
            roots.append(index)
        else:
            children[par].append(index)

    main = 0
    if main not in roots:
        return None

    outside_sides: Set[Side] = set()
    for root in roots:
        if root == main:
            continue
        if loops[root]:
            return None
        outside_sides.add(_outside_side(comps[root], comps[main]))

    med_kids = [kid for kid in children[main] if loops[kid]]
    leaf_kids = [kid for kid in children[main] if not loops[kid]]

    if not med_kids:
        if outside_sides:
            return None
        if not leaf_kids:
            return None
        return _render_leaves_only(len(leaf_kids), fg, bg)

    if len(med_kids) != 1:
        return None
    medium = med_kids[0]
    inner_leaves = [kid for kid in children[medium] if not loops[kid]]
    if any(loops[kid] for kid in children[medium]):
        return None
    if not inner_leaves:
        return None

    mcy, mcx = _centroid(comps[medium])
    leaf_sides: Set[Side] = set()
    for kid in leaf_kids:
        cy, cx = _centroid(comps[kid])
        leaf_sides.add(_dominant_side(cy - mcy, cx - mcx))

    return _render_with_medium(
        n_inner=len(inner_leaves),
        leaf_sides=leaf_sides,
        outside_sides=outside_sides,
        fg=fg,
        bg=bg,
    )


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("topology_schematic", topology_schematic)]


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
            "engine": "s1_topology_schematic",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_topology_schematic",
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
    "topology_schematic",
    "train_replay",
]
