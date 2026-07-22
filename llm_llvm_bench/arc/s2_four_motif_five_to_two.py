"""S2 four-motif 5→2 stamp (FoT).

Grammar (same_canvas_rewrite):
  Background is mostly color 5 with sparse color-4 motifs (8-connected).
  Each 4-motif stamps a small set of nearby 5-cells to color 2:
    - size-4 diamond → fill center
    - size-4 plus-minus-one (T) → fill missing ortho arm
    - size-3 V / chevron → fill notch + one step opposite the apex
    - size-2 diagonal / ortho domino → L-tromino / U stamp on the open side
  Licensed only on perfect train replay.

Canonical close: AGI-2 test task 14754a24.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]


def _eight_comps(g: Grid, col: int) -> List[List[Cell]]:
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    out: List[List[Cell]] = []
    nbrs = (
        (0, 1),
        (0, -1),
        (1, 0),
        (-1, 0),
        (1, 1),
        (1, -1),
        (-1, 1),
        (-1, -1),
    )
    for i in range(h):
        for j in range(w):
            if seen[i][j] or g[i][j] != col:
                continue
            q = deque([(i, j)])
            seen[i][j] = True
            cells: List[Cell] = []
            while q:
                r, c = q.popleft()
                cells.append((r, c))
                for dr, dc in nbrs:
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < h
                        and 0 <= cc < w
                        and not seen[rr][cc]
                        and g[rr][cc] == col
                    ):
                        seen[rr][cc] = True
                        q.append((rr, cc))
            out.append(cells)
    return out


def _targets_for_comp(comp: List[Cell]) -> Optional[List[Cell]]:
    s = set(comp)
    n = len(comp)
    rs = [r for r, _ in comp]
    cs = [c for _, c in comp]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)

    if n == 4 and (r1 - r0, c1 - c0) == (2, 2):
        cr, cc = (r0 + r1) // 2, (c0 + c1) // 2
        diamond = {(cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)}
        if (cr, cc) not in s and s == diamond:
            return [(cr, cc)]

    if n == 4:
        for r, c in comp:
            orth = sum(
                (r + dr, c + dc) in s for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0))
            )
            if orth == 3:
                for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    if (r + dr, c + dc) not in s:
                        return [(r + dr, c + dc)]

    if n == 3:
        byrow: Dict[int, List[int]] = {}
        for r, c in comp:
            byrow.setdefault(r, []).append(c)
        if len(byrow) == 2:
            rows = sorted(byrow)
            top, bot = rows[0], rows[1]
            if len(byrow[top]) == 2 and len(byrow[bot]) == 1:
                a, b = sorted(byrow[top])
                m = byrow[bot][0]
                if b - a == 2 and m == (a + b) // 2:
                    mid = (top, m)
                    ext = (top - 1, m)
                    return [mid, ext]
            if len(byrow[bot]) == 2 and len(byrow[top]) == 1:
                a, b = sorted(byrow[bot])
                m = byrow[top][0]
                if b - a == 2 and m == (a + b) // 2:
                    mid = (bot, m)
                    ext = (bot + 1, m)
                    return [mid, ext]

        for r, c in comp:
            n8 = sum(
                (r + dr, c + dc) in s
                for dr, dc in (
                    (0, 1),
                    (0, -1),
                    (1, 0),
                    (-1, 0),
                    (1, 1),
                    (1, -1),
                    (-1, 1),
                    (-1, -1),
                )
            )
            if n8 != 2:
                continue
            others = [p for p in comp if p != (r, c)]
            (r1_, c1_), (r2_, c2_) = others
            if r1_ == r2_ and abs(c1_ - c2_) == 2:
                mid = (r1_, (c1_ + c2_) // 2)
                ext = (mid[0] + (mid[0] - r), mid[1])
                return [mid, ext]
            if c1_ == c2_ and abs(r1_ - r2_) == 2:
                mid = ((r1_ + r2_) // 2, c1_)
                ext = (mid[0], mid[1] + (mid[1] - c))
                return [mid, ext]

    if n == 2:
        (r1, c1), (r2, c2) = sorted(comp)
        dr, dc = r2 - r1, c2 - c1
        if (dr, dc) == (1, -1):
            return [(r1 - 1, c1 - 1), (r1, c1 - 1), (r1, c1 - 2)]
        if (dr, dc) == (1, 1):
            return None  # resolved with canvas context in transform
        if (dr, dc) == (0, 1):
            return [(r1 - 1, c2), (r1, c2 + 1), (r1 + 1, c2)]
        if (dr, dc) == (1, 0):
            return [(r2, c1 - 1), (r2 + 1, c1), (r2, c1 + 1)]

    return []


def make_four_motif_five_to_two(
    marker: int = 4, fill_from: int = 5, fill_to: int = 2
) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        comps = _eight_comps(inp, marker)
        if not comps:
            return None
        out = [row[:] for row in inp]
        painted = False
        for comp in comps:
            t = _targets_for_comp(comp)
            if t is None and len(comp) == 2:
                (r1, c1), (r2, c2) = sorted(comp)
                if (r2 - r1, c2 - c1) == (1, 1):
                    cands = [
                        [(r1 - 1, c1 + 1), (r1, c1 + 1), (r1, c1 + 2)],
                        [(r2, c2 - 2), (r2, c2 - 1), (r2 + 1, c2 - 1)],
                    ]
                    best = None
                    best_sc = -1
                    for cand in cands:
                        sc = sum(
                            0 <= r < h and 0 <= c < w and inp[r][c] == fill_from
                            for r, c in cand
                        )
                        if sc > best_sc:
                            best_sc = sc
                            best = cand
                    t = best
            if not t:
                continue
            for r, c in t:
                if 0 <= r < h and 0 <= c < w and out[r][c] == fill_from:
                    out[r][c] = fill_to
                    painted = True
        return out if painted else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("four_motif_five_to_two", make_four_motif_five_to_two())]


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
            "engine": "s2_four_motif_five_to_two",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_four_motif_five_to_two",
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
