"""Batch FoT engine for eval task f560132c.

Grammar family owned here:
  g_f560132c (canonical: eval task f560132c)
    C4: licensed only on perfect train replay.

Modes:
  - 4-quadrant: palette 2x2 + three solids; perfect-tiling orientation search
  - 8-ring: palette 3x3 ring of 8 singletons + seven solids + hole;
    edge-flush perfect tiling over slot assignments

Never submits to Kaggle.
"""

from __future__ import annotations

from collections import Counter, deque
from itertools import permutations, product
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]


def g_f560132c(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


def _extract_components(grid: Grid) -> List[Dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps: List[Dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or seen[r][c]:
                continue
            stack = deque([(r, c)])
            seen[r][c] = True
            cells: List[Cell] = []
            cell_colors: Dict[Cell, int] = {}
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                cell_colors[(cr, cc)] = grid[cr][cc]
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] != 0:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            size = len(cells)
            centroid = (sum(rows) / size, sum(cols) / size)
            comps.append(
                {
                    "cells": cells,
                    "cell_colors": cell_colors,
                    "size": size,
                    "centroid": centroid,
                }
            )
    return comps


def _trimmed_mask(cells: List[Cell]) -> Grid:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    mask = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in cells:
        mask[r - r0][c - c0] = 1
    return mask


def _rotate_mask(mask: Grid, times: int) -> Grid:
    rotated = [row[:] for row in mask]
    for _ in range(times % 4):
        rotated = [list(row) for row in zip(*rotated[::-1])]
    return rotated


def _fill_holes(mask: Grid) -> Grid:
    h, w = len(mask), len(mask[0])
    seen = [[False] * w for _ in range(h)]
    q: deque = deque()
    for r in range(h):
        for c in (0, w - 1):
            if mask[r][c] == 0 and not seen[r][c]:
                seen[r][c] = True
                q.append((r, c))
    for c in range(w):
        for r in (0, h - 1):
            if mask[r][c] == 0 and not seen[r][c]:
                seen[r][c] = True
                q.append((r, c))
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and mask[nr][nc] == 0:
                seen[nr][nc] = True
                q.append((nr, nc))
    out = [row[:] for row in mask]
    for r in range(h):
        for c in range(w):
            if not seen[r][c]:
                out[r][c] = 1
    return out


def _compose(rotated: Dict[str, Grid], colours: Dict[str, int], out_h: int, out_w: int) -> Optional[Grid]:
    dims = {k: (len(v), len(v[0])) for k, v in rotated.items()}
    canvas = [[0] * out_w for _ in range(out_h)]
    placements = {
        "a": (0, 0),
        "b": (0, out_w - dims["b"][1]),
        "c": (out_h - dims["c"][0], 0),
        "d": (out_h - dims["d"][0], out_w - dims["d"][1]),
    }
    painted = 0
    overlap = 0
    target = sum(sum(sum(row) for row in rotated[k]) for k in "abcd")
    for key in "abcd":
        sr, sc = placements[key]
        colour = colours[key]
        mask = rotated[key]
        for r, row in enumerate(mask):
            for c, val in enumerate(row):
                if not val:
                    continue
                rr, cc = sr + r, sc + c
                if not (0 <= rr < out_h and 0 <= cc < out_w):
                    return None
                if canvas[rr][cc] != 0:
                    overlap += 1
                canvas[rr][cc] = colour
                painted += 1
    if overlap or painted != target:
        return None
    if any(v == 0 for row in canvas for v in row):
        return None
    return canvas


def _detect_ring(comp: Dict[str, Any]) -> Optional[Dict[Tuple[int, int], int]]:
    cc = comp["cell_colors"]
    counts = Counter(cc.values())
    uniq = {cell: col for cell, col in cc.items() if counts[col] == 1}
    if len(uniq) < 8:
        return None
    rs = [r for r, _ in uniq]
    cs = [c for _, c in uniq]
    for r0 in range(min(rs), max(rs) - 1):
        for c0 in range(min(cs), max(cs) - 1):
            rm: Dict[Tuple[int, int], int] = {}
            ok = True
            for dr in range(3):
                for dc in range(3):
                    if dr == 1 and dc == 1:
                        continue
                    cell = (r0 + dr, c0 + dc)
                    if cell not in uniq:
                        ok = False
                        break
                    rm[(dr, dc)] = uniq[cell]
                if not ok:
                    break
            if ok:
                return rm
    return None


def _solve_four(grid: Grid) -> Optional[Grid]:
    comps = _extract_components(grid)
    if len(comps) < 4:
        return None
    # palette = component containing global singletons or local 2x2 uniques
    counts = Counter(v for row in grid for v in row if v)
    global_singletons = {col for col, n in counts.items() if n == 1}
    pal = None
    block = None
    if len(global_singletons) == 4:
        pal_cells = [(r, c) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] in global_singletons]
        for comp in comps:
            if set(pal_cells).issubset(set(comp["cells"])):
                pal = comp
                break
        if pal is not None:
            min_r = min(r for r, _ in pal_cells)
            min_c = min(c for _, c in pal_cells)
            block = [[0, 0], [0, 0]]
            for r, c in pal_cells:
                block[r - min_r][c - min_c] = grid[r][c]
    if pal is None:
        best_score = -1
        for comp in comps:
            cc = comp["cell_colors"]
            cnt = Counter(cc.values())
            uniq = {col for col, n in cnt.items() if n == 1}
            by = {cell: cc[cell] for cell in cc if cc[cell] in uniq}
            for (r, c) in list(by):
                cells = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
                if all(x in by for x in cells):
                    score = len(uniq) + comp["size"]
                    if score > best_score:
                        best_score = score
                        pal = comp
                        block = [
                            [by[(r, c)], by[(r, c + 1)]],
                            [by[(r + 1, c)], by[(r + 1, c + 1)]],
                        ]
    if pal is None or block is None:
        return None
    solids = [c for c in comps if c is not pal and len(set(c["cell_colors"].values())) == 1]
    if len(solids) < 3:
        return None
    solids = sorted(solids, key=lambda c: -c["size"])[:3]

    def block_variants(b):
        outs = []
        mats = [
            b,
            [list(reversed(r)) for r in b],
            list(reversed(b)),
            [list(reversed(r)) for r in reversed(b)],
        ]
        for m in mats:
            bb = m
            for _ in range(4):
                outs.append({"a": bb[0][0], "b": bb[0][1], "c": bb[1][0], "d": bb[1][1]})
                bb = [[bb[1][0], bb[0][0]], [bb[1][1], bb[0][1]]]
        seen = set()
        res = []
        for o in outs:
            t = tuple(o[k] for k in "abcd")
            if t not in seen:
                seen.add(t)
                res.append(o)
        return res

    a_mask = _trimmed_mask(pal["cells"])
    target = pal["size"] + sum(c["size"] for c in solids)
    best = None
    for perm in permutations(solids):
        masks = {
            "a": a_mask,
            "b": _trimmed_mask(perm[0]["cells"]),
            "c": _trimmed_mask(perm[1]["cells"]),
            "d": _trimmed_mask(perm[2]["cells"]),
        }
        for orients in product(range(4), repeat=4):
            orientations = dict(zip("abcd", orients))
            rotated = {lab: _rotate_mask(masks[lab], orientations[lab]) for lab in "abcd"}
            dims = {k: (len(v), len(v[0])) for k, v in rotated.items()}
            mins_h = min(dims["a"][0] + dims["c"][0], dims["b"][0] + dims["d"][0])
            mins_w = min(dims["a"][1] + dims["b"][1], dims["c"][1] + dims["d"][1])
            side = int(round(target**0.5))
            heights = sorted({mins_h, side, max(mins_h, side)})
            widths = sorted({mins_w, side, max(mins_w, side), dims["a"][1] + dims["d"][1] - 1})
            for out_h in heights:
                for out_w in widths:
                    if out_h * out_w != target:
                        continue
                    for colmap in block_variants(block):
                        canvas = _compose(rotated, colmap, out_h, out_w)
                        if canvas is not None:
                            return canvas
    return best


def _edge_cands(slot: Tuple[int, int], mh: int, mw: int, S: int) -> List[Tuple[int, int]]:
    i, j = slot
    srs = [0] if i == 0 else ([S - mh] if i == 2 else list(range(0, S - mh + 1)))
    scs = [0] if j == 0 else ([S - mw] if j == 2 else list(range(0, S - mw + 1)))
    return [(sr, sc) for sr in srs for sc in scs]


def _solve_ring8(grid: Grid) -> Optional[Grid]:
    comps = _extract_components(grid)
    pal = None
    ring = None
    for comp in comps:
        rm = _detect_ring(comp)
        if rm is not None:
            pal, ring = comp, rm
            break
    if pal is None or ring is None:
        return None
    solids = [c for c in comps if c is not pal and c["size"] != 9]
    if len(solids) != 7:
        return None
    pal_mask = _fill_holes(_trimmed_mask(pal["cells"]))
    solid_masks = [_trimmed_mask(c["cells"]) for c in solids]
    total = sum(sum(sum(r) for r in m) for m in solid_masks) + sum(sum(r) for r in pal_mask)
    S = int(round((total + 9) ** 0.5))
    if S * S != total + 9:
        return None
    remain = [(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)]
    solid_rots = [[_rotate_mask(m, r) for r in range(4)] for m in solid_masks]
    pal_rots = [_rotate_mask(pal_mask, r) for r in range(4)]
    largest = max(range(7), key=lambda i: solids[i]["size"])
    left_idx = remain.index((1, 0))
    ordered = [p for p in permutations(range(7)) if p[left_idx] == largest]
    ordered += [p for p in permutations(range(7)) if p[left_idx] != largest]
    result: List[Optional[Grid]] = [None]

    def try_am(am: Dict[Tuple[int, int], Tuple[List[Grid], int]]) -> bool:
        items = sorted(am.items(), key=lambda kv: -sum(sum(r) for r in kv[1][0][0]))
        canvas = [[0] * S for _ in range(S)]

        def bt(i: int) -> bool:
            if i == len(items):
                if sum(canvas[r][c] == 0 for r in range(S) for c in range(S)) == 9:
                    result[0] = [row[:] for row in canvas]
                    return True
                return False
            slot, (rots, col) = items[i]
            for m in rots:
                mh, mw = len(m), len(m[0])
                cells = [(r, c) for r in range(mh) for c in range(mw) if m[r][c]]
                for sr, sc in _edge_cands(slot, mh, mw, S):
                    if any(canvas[sr + r][sc + c] != 0 for r, c in cells):
                        continue
                    for r, c in cells:
                        canvas[sr + r][sc + c] = col
                    if bt(i + 1):
                        return True
                    for r, c in cells:
                        canvas[sr + r][sc + c] = 0
            return False

        return bt(0)

    for perm in ordered:
        am = {(0, 0): (pal_rots, ring[(0, 0)])}
        for s, si in zip(remain, perm):
            am[s] = (solid_rots[si], ring[s])
        if try_am(am):
            return result[0]
    return None


def _solve(grid: Grid) -> Grid:
    comps = _extract_components(grid)
    for comp in comps:
        if _detect_ring(comp) is not None:
            out = _solve_ring8(grid)
            if out is not None:
                return out
            break
    out = _solve_four(grid)
    if out is None:
        raise ValueError("f560132c: no licensed tiling")
    return out


def named_candidates() -> List[Tuple[str, Transform]]:
    return [("g_f560132c", g_f560132c)]


def exact_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    out: List[Tuple[str, Transform]] = []
    for name, transform in named_candidates():
        if train and all(transform(ex["input"]) == ex["output"] for ex in train):
            out.append((name, transform))
    return out


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    train = task.get("train") or []
    exact = exact_candidates(train)
    if not exact:
        return {
            "engine": "s1_g_f560132c",
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
        "engine": "s1_g_f560132c",
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
    "g_f560132c",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
