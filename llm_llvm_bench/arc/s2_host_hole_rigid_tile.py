"""S2 host-hole rigid tile (FoT).

Grammar (same_canvas_rewrite):
  Color-5 cells are erased. Same-color 4-connected components that enclose
  one or more interior regions (not reachable from the border without
  crossing the component) are hosts; their walls stay. All other non-zero
  non-5 components are movers. Each mover keeps its shape and is rigidly
  translated so the movers exactly tile the host holes (exact cover).
  Licensed only on perfect train replay.

Canonical close: AGI-2 test task 184a9768.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]

_HINGE = 5
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _comps(inp: Grid, pred) -> List[List[Cell]]:
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    out: List[List[Cell]] = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or not pred(inp[r][c]):
                continue
            cells: List[Cell] = []
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in _DIRS:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and pred(inp[nr][nc])
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))
            out.append(cells)
    return out


def _interior(inp: Grid, wall_cells: Sequence[Cell]) -> List[Cell]:
    h, w = len(inp), len(inp[0])
    wall = set(wall_cells)
    q: deque[Cell] = deque()
    seen: Set[Cell] = set()
    for r in range(h):
        for c in (0, w - 1):
            if (r, c) not in wall and (r, c) not in seen:
                seen.add((r, c))
                q.append((r, c))
    for c in range(w):
        for r in (0, h - 1):
            if (r, c) not in wall and (r, c) not in seen:
                seen.add((r, c))
                q.append((r, c))
    while q:
        r, c = q.popleft()
        for dr, dc in _DIRS:
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < h
                and 0 <= nc < w
                and (nr, nc) not in seen
                and (nr, nc) not in wall
            ):
                seen.add((nr, nc))
                q.append((nr, nc))
    return [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) not in wall and (r, c) not in seen
    ]


def _hole_components(interior_cells: Sequence[Cell]) -> List[frozenset]:
    S = set(interior_cells)
    seen: Set[Cell] = set()
    holes: List[frozenset] = []
    for p in interior_cells:
        if p in seen:
            continue
        cells: List[Cell] = []
        q = deque([p])
        seen.add(p)
        while q:
            r, c = q.popleft()
            cells.append((r, c))
            for dr, dc in _DIRS:
                nr, nc = r + dr, c + dc
                if (nr, nc) in S and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    q.append((nr, nc))
        holes.append(frozenset(cells))
    return holes


def _norm_shape(cells: Sequence[Cell]) -> frozenset:
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _placements(shape: frozenset, hole: frozenset) -> List[frozenset]:
    hole_set = set(hole)
    sh = list(shape)
    out: List[frozenset] = []
    seen: Set[frozenset] = set()
    for hr, hc in hole:
        for sr, sc in sh:
            dr, dc = hr - sr, hc - sc
            placed = frozenset((r + dr, c + dc) for r, c in sh)
            if placed <= hole_set and placed not in seen:
                seen.add(placed)
                out.append(placed)
    return out


def _host_hole_rigid_tile(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    colors = sorted({v for row in inp for v in row} - {0, _HINGE})
    hosts: List[Tuple[int, List[Cell], List[frozenset]]] = []
    movers: List[Tuple[int, frozenset, Cell]] = []
    for col in colors:
        for cells in _comps(inp, lambda v, col=col: v == col):
            inter = _interior(inp, cells)
            if inter:
                hosts.append((col, cells, _hole_components(inter)))
            else:
                movers.append((col, _norm_shape(cells), min(cells)))
    if not hosts or not movers:
        return None
    holes: List[frozenset] = []
    for _, _, hs in hosts:
        holes.extend(hs)
    if sum(len(x) for x in holes) != sum(len(m[1]) for m in movers):
        return None

    n_m, n_h = len(movers), len(holes)
    place_opts: List[List[Tuple[int, frozenset]]] = []
    for col, shape, _pos in movers:
        opts: List[Tuple[int, frozenset]] = []
        for hi, hole in enumerate(holes):
            if len(shape) > len(hole):
                continue
            for pl in _placements(shape, hole):
                opts.append((hi, pl))
        if not opts:
            return None
        place_opts.append(opts)

    order = sorted(range(n_m), key=lambda i: (-len(movers[i][1]), movers[i][2]))
    hole_occ: List[Dict[Cell, int]] = [{} for _ in range(n_h)]
    saved: Optional[List[Dict[Cell, int]]] = None

    def bt(k: int) -> bool:
        nonlocal saved
        if saved is not None:
            return True
        if k == n_m:
            if all(len(hole_occ[hi]) == len(holes[hi]) for hi in range(n_h)):
                saved = [dict(d) for d in hole_occ]
                return True
            return False
        mi = order[k]
        col = movers[mi][0]
        for hi, pl in place_opts[mi]:
            if any(cell in hole_occ[hi] for cell in pl):
                continue
            for cell in pl:
                hole_occ[hi][cell] = col
            if len(hole_occ[hi]) <= len(holes[hi]) and bt(k + 1):
                return True
            for cell in pl:
                del hole_occ[hi][cell]
        return False

    if not bt(0) or saved is None:
        return None

    out = [row[:] for row in inp]
    mover_cells: Set[Cell] = set()
    for col in colors:
        for cells in _comps(inp, lambda v, col=col: v == col):
            if not _interior(inp, cells):
                mover_cells.update(cells)
    for r, c in mover_cells:
        out[r][c] = 0
    for r in range(h):
        for c in range(w):
            if out[r][c] == _HINGE:
                out[r][c] = 0
    for occ in saved:
        for (r, c), col in occ.items():
            out[r][c] = col
    return out


def make_host_hole_rigid_tile() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _host_hole_rigid_tile(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("host_hole_rigid_tile", make_host_hole_rigid_tile())]


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
            "engine": "s2_host_hole_rigid_tile",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_host_hole_rigid_tile",
        "train_replay": f"{passed}/{len(train)}",
        "perfect": passed == len(train) and len(train) > 0,
        "passed": passed,
        "total": len(train),
        "licensed_transforms": [n for n, _ in exact],
        "primary_transform": name,
    }


def solve_task(task: Dict[str, Any]) -> Optional[List[Dict[str, Grid]]]:
    if not train_replay(task)["perfect"]:
        return None
    _, transform = exact_candidates(task["train"])[0]
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
]
