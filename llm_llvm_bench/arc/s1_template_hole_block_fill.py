"""S1 template hole block-fill language game (FoT).

Grammar family owned here:
  template_hole_block_fill (canonical: eval task 898e7135)
    S1: output canvas is template bbox scaled by N (cell→N×N).
    S2: largest same-color component = template; black holes inside bbox.
    S3: remaining components with area≥4 are colored blocks at N× scale.
    S4: match hole shapes to reduced block shapes under D4×reflect;
        paint holes with matched colors at scale N.
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 898e7135). Never submits to Kaggle.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Point = Tuple[int, int]


def template_hole_block_fill(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


def _normalize(s: Set[Point] | frozenset) -> frozenset:
    r0 = min(r for r, _ in s)
    c0 = min(c for _, c in s)
    return frozenset((r - r0, c - c0) for r, c in s)


def _all_orientations(s: frozenset) -> set:
    pts = list(s)
    results = set()
    for _ in range(4):
        results.add(_normalize(frozenset(pts)))
        pts = [(c, -r) for r, c in pts]
    pts = [(r, -c) for r, c in list(s)]
    for _ in range(4):
        results.add(_normalize(frozenset(pts)))
        pts = [(c, -r) for r, c in pts]
    return results


def _detect_scale(raw_blocks, holes) -> int:
    hole_orients: set = set()
    for h in holes:
        hole_orients.update(_all_orientations(_normalize(h)))
    for scale in range(2, 10):
        matched = 0
        for _bcolor, bcomp in raw_blocks:
            br0 = min(r for r, _ in bcomp)
            bc0 = min(c for _, c in bcomp)
            reduced = {((r - br0) // scale, (c - bc0) // scale) for r, c in bcomp}
            if _normalize(reduced) in hole_orients:
                matched += 1
        if matched == len(raw_blocks):
            return scale
    return 2


def _solve(grid: Grid) -> Grid:
    height, width = len(grid), len(grid[0])
    visited: set[Point] = set()
    components: List[Tuple[int, Set[Point]]] = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] != 0 and (r, c) not in visited:
                color = grid[r][c]
                comp: Set[Point] = set()
                queue: deque[Point] = deque([(r, c)])
                while queue:
                    cr, cc = queue.popleft()
                    if (cr, cc) in visited or grid[cr][cc] != color:
                        continue
                    visited.add((cr, cc))
                    comp.add((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if (
                            0 <= nr < height
                            and 0 <= nc < width
                            and (nr, nc) not in visited
                            and grid[nr][nc] == color
                        ):
                            queue.append((nr, nc))
                components.append((color, comp))

    components.sort(key=lambda x: len(x[1]), reverse=True)
    tmpl_color, tmpl_cells = components[0]
    tr0 = min(r for r, _ in tmpl_cells)
    tc0 = min(c for _, c in tmpl_cells)
    tr1 = max(r for r, _ in tmpl_cells)
    tc1 = max(c for _, c in tmpl_cells)
    tmpl_h = tr1 - tr0 + 1
    tmpl_w = tc1 - tc0 + 1
    tmpl = [
        [grid[tr0 + r][tc0 + c] for c in range(tmpl_w)] for r in range(tmpl_h)
    ]

    hole_vis: set[Point] = set()
    holes: List[Set[Point]] = []
    for r in range(tmpl_h):
        for c in range(tmpl_w):
            if tmpl[r][c] == 0 and (r, c) not in hole_vis:
                region: Set[Point] = set()
                queue = deque([(r, c)])
                while queue:
                    cr, cc = queue.popleft()
                    if (cr, cc) in hole_vis:
                        continue
                    hole_vis.add((cr, cc))
                    region.add((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if (
                            0 <= nr < tmpl_h
                            and 0 <= nc < tmpl_w
                            and (nr, nc) not in hole_vis
                            and tmpl[nr][nc] == 0
                        ):
                            queue.append((nr, nc))
                holes.append(region)

    raw_blocks = [
        (bcolor, bcomp)
        for bcolor, bcomp in components[1:]
        if len(bcomp) >= 4
    ]
    scale = _detect_scale(raw_blocks, holes)

    blocks = []
    for bcolor, bcomp in raw_blocks:
        br0 = min(r for r, _ in bcomp)
        bc0 = min(c for _, c in bcomp)
        reduced = {((r - br0) // scale, (c - bc0) // scale) for r, c in bcomp}
        blocks.append((bcolor, _normalize(reduced)))

    hole_color: Dict[int, int] = {}
    used: set[int] = set()
    for hi, region in enumerate(holes):
        nreg = _normalize(region)
        for bi, (bc, bs) in enumerate(blocks):
            if bi in used or len(bs) != len(nreg):
                continue
            if nreg in _all_orientations(bs):
                hole_color[hi] = bc
                used.add(bi)
                break

    oh, ow = tmpl_h * scale, tmpl_w * scale
    out = [[tmpl_color] * ow for _ in range(oh)]
    for hi, region in enumerate(holes):
        color = hole_color.get(hi, 0)
        for r, col in region:
            for dr in range(scale):
                for dc in range(scale):
                    out[r * scale + dr][col * scale + dc] = color
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("template_hole_block_fill", template_hole_block_fill)]


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
            "engine": "s1_template_hole_block_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_template_hole_block_fill",
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
    "template_hole_block_fill",
    "train_replay",
]
