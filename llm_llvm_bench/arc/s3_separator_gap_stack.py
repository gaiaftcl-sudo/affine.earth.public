"""S3 separator gap-stack language game (FoT).

Grammar family owned here:
  separator_gap_stack (canonical: eval task 16b78196)
    S1: same canvas shape (in-place rewrite); thick H or V separator band.
    S2: movable objects = 4-connected comps excluding separator color.
    S3: tight vertical (band-normal) nests with high contact form Kruskal
        forests → rigid stack assemblies (transpose when band is vertical).
    S4: dock each assembly onto the separator by maximizing gap penetration
        then contact, then proximity to band center.
    C4: exact rewritten grid; licensed only when every training pair replays.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell3 = Tuple[int, int, int]

CONTACT_MIN = 5


def _find_band(grid: Grid) -> Optional[Tuple[int, int, int, str]]:
    """Return (a, b, color, 'H'|'V') for the dominant thick separator band."""
    height, width = len(grid), len(grid[0])
    best: Optional[Tuple[int, int, int, int, str]] = None
    for color in range(1, 10):
        rows = [
            row
            for row in range(height)
            if sum(1 for col in range(width) if grid[row][col] == color) >= width // 2
        ]
        if rows:
            start = prev = rows[0]
            for row in rows[1:] + [None]:
                if row is not None and row == prev + 1:
                    prev = row
                    continue
                score = (prev - start + 1) * sum(
                    grid[rr][col] == color
                    for rr in range(start, prev + 1)
                    for col in range(width)
                )
                if best is None or score > best[0]:
                    best = (score, start, prev, color, "H")
                if row is not None:
                    start = prev = row
        cols = [
            col
            for col in range(width)
            if sum(1 for row in range(height) if grid[row][col] == color)
            >= height // 2
        ]
        if cols:
            start = prev = cols[0]
            for col in cols[1:] + [None]:
                if col is not None and col == prev + 1:
                    prev = col
                    continue
                score = (prev - start + 1) * sum(
                    grid[row][cc] == color
                    for row in range(height)
                    for cc in range(start, prev + 1)
                )
                if best is None or score > best[0]:
                    best = (score, start, prev, color, "V")
                if col is not None:
                    start = prev = col
    if best is None:
        return None
    _, a, b, color, orient = best
    return a, b, color, orient


def _extract_objects(grid: Grid, sep_color: int) -> List[List[Cell3]]:
    height, width = len(grid), len(grid[0])
    seen = [[False] * width for _ in range(height)]
    out: List[List[Cell3]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] in (0, sep_color) or seen[row][col]:
                continue
            queue: deque[Tuple[int, int]] = deque([(row, col)])
            seen[row][col] = True
            cells: List[Cell3] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc, grid[rr][cc]))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] not in (0, sep_color)
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))
            out.append(cells)
    return out


def _normalize(cells: Sequence[Cell3]) -> List[Cell3]:
    r0 = min(r for r, _, _ in cells)
    c0 = min(c for _, c, _ in cells)
    return [(r - r0, c - c0, v) for r, c, v in cells]


def _best_tight_vertical_nest(
    a_norm: Sequence[Cell3], b_norm: Sequence[Cell3]
) -> Optional[Tuple[int, int]]:
    """Return (contact, dr) for best tight vertical nest of b onto a, or None."""
    a_cells = {(r, c) for r, c, _ in a_norm}
    best: Optional[Tuple[int, int, int]] = None  # contact, -vgap, dr
    for dr in range(-20, 21):
        b_cells = {(r + dr, c) for r, c, _ in b_norm}
        if a_cells & b_cells:
            continue
        contact = sum(
            1
            for r, c in b_cells
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            if (nr, nc) in a_cells
        )
        if contact == 0:
            continue
        ar0 = min(r for r, _ in a_cells)
        ar1 = max(r for r, _ in a_cells)
        br0 = min(r for r, _ in b_cells)
        br1 = max(r for r, _ in b_cells)
        if ar1 < br0:
            vgap = br0 - ar1 - 1
        elif br1 < ar0:
            vgap = ar0 - br1 - 1
        else:
            vgap = 0
        if vgap != 0:
            continue
        cand = (contact, -vgap, dr)
        if best is None or cand > best:
            best = cand
    if best is None:
        return None
    return best[0], best[2]


def _transpose(grid: Grid) -> Grid:
    return [[grid[r][c] for r in range(len(grid))] for c in range(len(grid[0]))]


def separator_gap_stack(grid: Grid) -> Optional[Grid]:
    meta = _find_band(grid)
    if meta is None:
        return None
    a, b, sep, orient = meta
    work = grid
    transposed = False
    if orient == "V":
        work = _transpose(grid)
        transposed = True
        meta2 = _find_band(work)
        if meta2 is None:
            return None
        a, b, sep, orient = meta2
        if orient != "H":
            return None

    height, width = len(work), len(work[0])
    objects = _extract_objects(work, sep)
    if not objects:
        return [list(row) for row in grid]

    norms = [_normalize(obj) for obj in objects]
    edges: List[Tuple[int, int, int, int]] = []
    for i, a_norm in enumerate(norms):
        for j, b_norm in enumerate(norms):
            if i == j:
                continue
            nest = _best_tight_vertical_nest(a_norm, b_norm)
            if nest is None:
                continue
            contact, dr = nest
            if contact < CONTACT_MIN:
                continue
            edges.append((contact, i, j, dr))
    edges.sort(reverse=True)

    parent = list(range(len(objects)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    chosen: List[Tuple[int, int, int, int]] = []
    for contact, i, j, dr in edges:
        ri, rj = find(i), find(j)
        if ri == rj:
            continue
        parent[rj] = ri
        chosen.append((contact, i, j, dr))

    comps: Dict[int, List[int]] = defaultdict(list)
    for index in range(len(objects)):
        comps[find(index)].append(index)

    assemblies: List[List[Cell3]] = []
    for comp in comps.values():
        root = min(comp)
        pos: Dict[int, Tuple[int, int]] = {root: (0, 0)}
        und: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
        for _contact, i, j, dr in chosen:
            if i in comp and j in comp:
                und[i].append((j, dr))
                und[j].append((i, -dr))
        queue: deque[int] = deque([root])
        while queue:
            u = queue.popleft()
            for v, dr in und[u]:
                if v in pos:
                    continue
                pr, pc = pos[u]
                pos[v] = (pr + dr, pc)
                queue.append(v)
        for index in comp:
            if index not in pos:
                pos[index] = (0, 0)
        cells: List[Cell3] = []
        for index in comp:
            dr, dc = pos[index]
            cells.extend((r + dr, c + dc, v) for r, c, v in norms[index])
        if not cells:
            continue
        r0 = min(r for r, _, _ in cells)
        c0 = min(c for _, c, _ in cells)
        assemblies.append([(r - r0, c - c0, v) for r, c, v in cells])

    canvas = [
        [work[r][c] if work[r][c] == sep else 0 for c in range(width)]
        for r in range(height)
    ]
    orig_gap = [
        [a <= r <= b and work[r][c] == 0 for c in range(width)] for r in range(height)
    ]

    def can_place(cells: Sequence[Cell3], tr: int, tc: int) -> bool:
        for r, c, _v in cells:
            rr, cc = r + tr, c + tc
            if not (0 <= rr < height and 0 <= cc < width):
                return False
            if canvas[rr][cc] != 0:
                return False
        return True

    def touches(cells: Sequence[Cell3], tr: int, tc: int) -> bool:
        for r, c, _v in cells:
            rr, cc = r + tr, c + tc
            for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                if 0 <= nr < height and 0 <= nc < width and canvas[nr][nc] != 0:
                    return True
        return False

    def gap_pen(cells: Sequence[Cell3], tr: int, tc: int) -> int:
        return sum(1 for r, c, _v in cells if orig_gap[r + tr][c + tc])

    assemblies.sort(key=lambda cells: -len(cells))
    for cells in assemblies:
        best: Optional[Tuple[Tuple[Any, ...], int, int]] = None
        for tr in range(height):
            for tc in range(width):
                if not can_place(cells, tr, tc):
                    continue
                if not touches(cells, tr, tc):
                    continue
                gp = gap_pen(cells, tr, tc)
                contact = 0
                for r, c, _v in cells:
                    rr, cc = r + tr, c + tc
                    for nr, nc in (
                        (rr - 1, cc),
                        (rr + 1, cc),
                        (rr, cc - 1),
                        (rr, cc + 1),
                    ):
                        if 0 <= nr < height and 0 <= nc < width and canvas[nr][nc] != 0:
                            contact += 1
                cr = sum(r + tr for r, _, _ in cells) / len(cells)
                score = (-gp, -contact, abs(cr - (a + b) / 2), tr, tc)
                if best is None or score < best[0]:
                    best = (score, tr, tc)
        if best is None:
            continue
        _score, tr, tc = best
        for r, c, v in cells:
            canvas[r + tr][c + tc] = v

    if transposed:
        return _transpose(canvas)
    return canvas


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("separator_gap_stack", separator_gap_stack)]


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
            "engine": "s3_separator_gap_stack",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_separator_gap_stack",
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
    "separator_gap_stack",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
