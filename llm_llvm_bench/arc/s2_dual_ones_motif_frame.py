"""S2 dual-ones motif frame (FoT).

Grammar (same_canvas_rewrite):
  Two equal 1-blocks are opposite corners of a rectangle. Dominant color is
  background. Horizontal motif is the row-suffix right of the top-left block;
  tile motif(+bg) between the blocks on the shared rows, and stamp a bar of
  the motif's first non-bg color above/below. Vertical: two solid colors under
  the top-left block drive a period-4 side rail (full side / rail / insert /
  rail) on outside rails. Licensed only on perfect train replay.

Canonical close: AGI-2 test task 34cfa167.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _comps(grid: Grid, col: int) -> List[List[Tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    out: List[List[Tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or grid[r][c] != col:
                continue
            cells: List[Tuple[int, int]] = []
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and grid[nr][nc] == col
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))
            out.append(cells)
    return out


def _apply(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    bg = Counter(c for row in inp for c in row).most_common(1)[0][0]
    ones = _comps(inp, 1)
    if len(ones) != 2:
        return None
    ones = sorted(
        ones, key=lambda cells: (min(r for r, _ in cells), min(c for _, c in cells))
    )
    a, b = ones
    ar0, ar1 = min(r for r, _ in a), max(r for r, _ in a)
    ac0, ac1 = min(c for _, c in a), max(c for _, c in a)
    br0, br1 = min(r for r, _ in b), max(r for r, _ in b)
    bc0, bc1 = min(c for _, c in b), max(c for _, c in b)
    if ar0 > br0:
        ar0, ar1, ac0, ac1, br0, br1, bc0, bc1 = (
            br0,
            br1,
            bc0,
            bc1,
            ar0,
            ar1,
            ac0,
            ac1,
        )
    bh, bw = ar1 - ar0 + 1, ac1 - ac0 + 1
    if (br1 - br0 + 1, bc1 - bc0 + 1) != (bh, bw):
        return None
    if ac0 == 0 or bc1 + 1 >= w or bc0 <= ac1:
        return None

    maxc = ac1
    for r in range(ar0, ar1 + 1):
        for c in range(ac1 + 1, bc0):
            if inp[r][c] != bg:
                maxc = max(maxc, c)
    if maxc <= ac1:
        return None
    motif = list(inp[ar0][ac1 + 1 : maxc + 1])
    tile = motif + [bg] if (not motif or motif[-1] != bg) else list(motif)
    mid_len = bc0 - (ac1 + 1)
    mid: List[int] = []
    while len(mid) < mid_len:
        mid.extend(tile)
    mid = mid[:mid_len]

    vcols: List[int] = []
    for r in range(ar1 + 1, br0):
        seg = inp[r][ac0 : ac1 + 1]
        cols = [v for v in seg if v != bg]
        if cols and len(set(cols)) == 1:
            vcols.append(cols[0])
    uniq: List[int] = []
    for c in vcols:
        if c not in uniq:
            uniq.append(c)
    if not uniq:
        return None
    c_side = uniq[0]
    c_ins = uniq[1] if len(uniq) > 1 else uniq[0]

    out = [[bg] * w for _ in range(h)]
    row_pat = [1] * bw + mid + [1] * bw
    for dr in range(bh):
        for i, v in enumerate(row_pat):
            out[ar0 + dr][ac0 + i] = v
            out[br0 + dr][ac0 + i] = v

    bar_color = next((v for v in motif if v != bg), None)
    if bar_color is not None:
        if ar0 - 1 >= 0:
            for c in range(ac1 + 1, bc0):
                out[ar0 - 1][c] = bar_color
        if br1 + 1 < h:
            for c in range(ac1 + 1, bc0):
                out[br1 + 1][c] = bar_color

    left_rail, right_rail = ac0 - 1, bc1 + 1
    left_cols = list(range(ac0 - 1, ac1 + 1))
    right_cols = list(range(bc0, bc1 + 2))
    for r in range(ar1 + 1, br0):
        off = (r - (ar1 + 1)) % 4
        if off == 0:
            for c in left_cols + right_cols:
                out[r][c] = c_side
        elif off in (1, 3):
            out[r][left_rail] = c_side
            out[r][right_rail] = c_side
        else:
            out[r][left_rail] = c_side
            out[r][right_rail] = c_side
            for c in range(ac0, ac1 + 1):
                out[r][c] = c_ins
            for c in range(bc0, bc1 + 1):
                out[r][c] = c_ins
    return out


def make_dual_ones_motif_frame() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _apply(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("dual_ones_motif_frame", make_dual_ones_motif_frame())]


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
            "engine": "s2_dual_ones_motif_frame",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_dual_ones_motif_frame",
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
