"""S2 eight-block diagonal-2 thick-4 corridors (FoT).

Grammar (same_canvas_rewrite):
  Color-8 solid block bbox. Paint 2 on four corner diagonals outward until a
  nonzero cell or a cell with king-neighbor count of 5s >= 3. Then paint 4:
  (1) gap-1 pair bridges of 5s aligned to block columns; (2) one thick diagonal
  corridor per active corner quadrant from selected 5 sources (NE/NW parallel
  or inward-adj, SW K+2 band, SE orth-adj with two free vertical steps);
  (3) orth touch cells from non-pair mb<=2 side 5s. Licensed only on perfect
  train replay.

Canonical close: AGI-2 test task 212895b5.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_DIRS8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
_ORTH = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_RAYS = [("NW", -1, -1), ("NE", -1, 1), ("SW", 1, -1), ("SE", 1, 1)]


def _block(g: Grid) -> Tuple[int, int, int, int]:
    cells = [(r, c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c] == 8]
    return (
        min(r for r, _ in cells),
        max(r for r, _ in cells),
        min(c for _, c in cells),
        max(c for _, c in cells),
    )


def _k5(g: Grid, r: int, c: int) -> int:
    h, w = len(g), len(g[0])
    return sum(
        1
        for dr, dc in _DIRS8
        if 0 <= r + dr < h and 0 <= c + dc < w and g[r + dr][c + dc] == 5
    )


def _twos(g: Grid):
    b = _block(g)
    h, w = len(g), len(g[0])
    r0, r1, c0, c1 = b
    p: set = set()
    rays = {}
    corners = {"NW": (r0, c0), "NE": (r0, c1), "SW": (r1, c0), "SE": (r1, c1)}
    for name, dr, dc in _RAYS:
        r, c = corners[name]
        rr, cc = r + dr, c + dc
        cells = []
        while 0 <= rr < h and 0 <= cc < w:
            if g[rr][cc] != 0:
                break
            if _k5(g, rr, cc) >= 3:
                break
            cells.append((rr, cc))
            p.add((rr, cc))
            rr += dr
            cc += dc
        k = None
        if cells:
            k = (
                (cells[0][0] + cells[0][1])
                if name in ("NE", "SW")
                else (cells[0][0] - cells[0][1])
            )
        rays[name] = {"cells": cells, "dr": dr, "dc": dc, "K": k}
    return p, rays, b


def _mb(r: int, c: int, b: Tuple[int, int, int, int]) -> int:
    r0, r1, c0, c1 = b
    dr = 0 if r0 <= r <= r1 else (r0 - r if r < r0 else r - r1)
    dc = 0 if c0 <= c <= c1 else (c0 - c if c < c0 else c - c1)
    return max(dr, dc)


def _touches(r: int, c: int, b: Tuple[int, int, int, int]) -> bool:
    r0, r1, c0, c1 = b
    return any(
        r0 <= r + dr <= r1 and c0 <= c + dc <= c1 for dr, dc in _DIRS8
    )


def _free(g: Grid, r: int, c: int, p2: set) -> bool:
    h, w = len(g), len(g[0])
    return 0 <= r < h and 0 <= c < w and g[r][c] == 0 and (r, c) not in p2


def _sgn(x: int) -> int:
    return 0 if x == 0 else (1 if x > 0 else -1)


def _nearest(r: int, c: int, b: Tuple[int, int, int, int]) -> Tuple[int, int]:
    r0, r1, c0, c1 = b
    return min(max(r, r0), r1), min(max(c, c0), c1)


def _d2n(r: int, c: int, cells) -> int:
    if not cells:
        return 99
    return min(max(abs(r - pr), abs(c - pc)) for pr, pc in cells)


def _quad(r: int, c: int, b: Tuple[int, int, int, int]) -> Optional[str]:
    r0, r1, c0, c1 = b
    if r < r0 and c < c0:
        return "NW"
    if r < r0 and c > c1:
        return "NE"
    if r > r1 and c < c0:
        return "SW"
    if r > r1 and c > c1:
        return "SE"
    return None


def _inside(cell, q: str, rays) -> bool:
    info = rays[q]
    if info["K"] is None:
        return True
    r, c = cell
    k = info["K"]
    return {
        "NE": r + c < k,
        "SW": r + c > k,
        "NW": r - c > k,
        "SE": r - c < k,
    }[q]


def _thick(st, dr, dc, g, p2, b, ph):
    path = []
    rr, cc = st
    while 0 <= rr < len(g) and 0 <= cc < len(g[0]) and _free(g, rr, cc, p2):
        path.append((rr, cc))
        if _touches(rr, cc, b):
            break
        rr += dr
        cc += dc
    if not path:
        return set()
    paint = set(path)
    last = len(path) - 1
    if dr and dc:
        for i, (r, c) in enumerate(path):
            if i == last and _touches(r, c, b):
                continue
            er, ec = (r + dr, c) if i % 2 == ph else (r, c + dc)
            if _free(g, er, ec, p2):
                paint.add((er, ec))
    return paint


def _phase_for(st, src) -> int:
    r, c = st
    sr, sc = src
    if sr == r:
        return (r + c) % 2
    if sc == c:
        return r % 2
    return 1 - ((r + c) % 2)


def _pick_start(src, g, b, p2):
    sr, sc = src
    br, bc = _nearest(sr, sc, b)
    dr, dc = _sgn(br - sr), _sgn(bc - sc)
    if not (dr and dc):
        return None
    eq = []
    diag = None
    for sdr, sdc in _ORTH:
        if (sdr and sdr != dr) or (sdc and sdc != dc):
            continue
        rr, cc = sr + sdr, sc + sdc
        if _free(g, rr, cc, p2) and _mb(rr, cc, b) == _mb(sr, sc, b):
            eq.append((rr, cc))
    if _free(g, sr + dr, sc + dc, p2) and _mb(sr + dr, sc + dc, b) < _mb(sr, sc, b):
        diag = (sr + dr, sc + dc)
    adj2 = [
        (sr + ddr, sc + ddc)
        for ddr, ddc in _DIRS8
        if 0 <= sr + ddr < len(g)
        and 0 <= sc + ddc < len(g[0])
        and (sr + ddr, sc + ddc) in p2
    ]
    diag_adj = any(abs(ar - sr) == 1 and abs(ac - sc) == 1 for ar, ac in adj2)
    row_adj = any(ar == sr and ac != sc for ar, ac in adj2)
    col_adj = any(ac == sc and ar != sr for ar, ac in adj2)
    vert = [e for e in eq if e[1] == sc]
    horiz = [e for e in eq if e[0] == sr]
    if diag_adj and diag is not None:
        st = diag
    elif row_adj and vert:
        st = vert[0]
    elif col_adj and horiz:
        st = horiz[0]
    elif eq:
        st = eq[0]
    else:
        st = diag
    if st is None:
        return None
    return st, dr, dc, _phase_for(st, src), (st == diag)


def _se_two_steps(src, g, b, p2) -> bool:
    sr, sc = src
    r0, r1, _, _ = b
    step = -1 if sr > r1 else (1 if sr < r0 else 0)
    if step == 0:
        return False
    return _free(g, sr + step, sc, p2) and _free(g, sr + 2 * step, sc, p2)


def _apply(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    eights = sum(1 for row in inp for v in row if v == 8)
    if eights < 4:
        return None
    try:
        p2, rays, b = _twos(inp)
    except ValueError:
        return None
    h, w = len(inp), len(inp[0])
    r0, r1, c0, c1 = b
    fives = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == 5]
    pair_fives: set = set()
    by_row: Dict[int, List[int]] = defaultdict(list)
    for r, c in fives:
        by_row[r].append(c)
    for r, cols in by_row.items():
        cols = sorted(set(cols))
        for i in range(len(cols) - 1):
            if cols[i + 1] - cols[i] == 2 and c0 <= cols[i] + 1 <= c1:
                pair_fives.add((r, cols[i]))
                pair_fives.add((r, cols[i + 1]))

    p4: set = set()
    byq: Dict[str, List[Tuple[int, int]]] = defaultdict(list)
    for r, c in fives:
        q = _quad(r, c, b)
        if not q or not rays[q]["cells"]:
            continue
        info = rays[q]
        odr, odc = info["dr"], info["dc"]
        k = info["K"]
        ok = False
        has_adj2 = False
        has_orth_adj2 = False
        has_diag_adj2 = False
        for pr, pc in info["cells"]:
            if max(abs(pr - r), abs(pc - c)) == 1 and (_sgn(r - pr), _sgn(c - pc)) != (
                odr,
                odc,
            ):
                ok = True
                has_adj2 = True
                if abs(pr - r) + abs(pc - c) == 1:
                    has_orth_adj2 = True
                if abs(pr - r) == 1 and abs(pc - c) == 1:
                    has_diag_adj2 = True
        if k is not None:
            if q == "NE" and r + c in (k - 1, k - 2):
                ok = True
            if q == "NW" and r - c in (k + 1, k + 2):
                ok = True
            if q == "SW" and r + c == k + 2 and has_adj2 and 4 <= _mb(r, c, b) <= 7:
                ok = True
            elif q == "SW":
                ok = False
            if (
                q == "SE"
                and has_orth_adj2
                and not has_diag_adj2
                and _mb(r, c, b) <= 2
                and _se_two_steps((r, c), inp, b, p2)
            ):
                ok = True
            elif q == "SE":
                ok = False
        if q == "NW" and ok:
            d2 = _d2n(r, c, info["cells"])
            if d2 > 1 and len(info["cells"]) > 2:
                ok = False
        if not ok:
            continue
        byq[q].append((r, c))

    for q, srcs in byq.items():
        best = None
        for src in srcs:
            ch = _pick_start(src, inp, b, p2)
            if not ch:
                continue
            st, dr, dc, ph, is_diag = ch
            paint = _thick(st, dr, dc, inp, p2, b, ph)
            if is_diag:
                sr, sc = src
                corners = [
                    cell
                    for cell in ((sr, sc + dc), (sr + dr, sc))
                    if _free(inp, cell[0], cell[1], p2)
                ]
                if corners:
                    paint.add(max(corners, key=lambda rc: _mb(rc[0], rc[1], b)))
            if not paint or not any(_touches(x, y, b) for x, y in paint):
                continue
            if any(not _inside(cell, q, rays) for cell in paint):
                continue
            key = (_mb(src[0], src[1], b), -len(paint))
            if best is None or key < best[0]:
                best = (key, src, paint)
        if best:
            p4 |= best[2]

    for r, cols in by_row.items():
        if r0 <= r <= r1:
            continue
        cols = sorted(set(cols))
        for i in range(len(cols) - 1):
            a, bc = cols[i], cols[i + 1]
            if bc - a != 2:
                continue
            mid = a + 1
            if c0 <= mid <= c1 and _free(inp, r, mid, p2):
                p4.add((r, mid))
                step = 1 if r < r0 else -1
                if _free(inp, r + step, mid, p2):
                    p4.add((r + step, mid))

    for r, c in fives:
        if (r, c) in pair_fives:
            continue
        if _mb(r, c, b) > 2:
            continue
        for dr, dc in _ORTH:
            rr, cc = r + dr, c + dc
            if _free(inp, rr, cc, p2) and _touches(rr, cc, b) and _mb(rr, cc, b) < _mb(r, c, b):
                p4.add((rr, cc))

    out = [row[:] for row in inp]
    for r, c in p2:
        out[r][c] = 2
    for r, c in p4:
        if out[r][c] == 0:
            out[r][c] = 4
    return out


def make_eight_block_diag2_thick4() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _apply(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("eight_block_diag2_thick4", make_eight_block_diag2_thick4())]


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
            "engine": "s2_eight_block_diag2_thick4",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_eight_block_diag2_thick4",
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
