"""S2 dual-anchor pingpong frame (FoT).

Grammar (same_canvas_rewrite):
  Two 1-blocks act as diagonal anchors. Decorations nearer the top-left anchor
  define horizontal and vertical color sequences (including background gaps).
  Place 1-blocks at all four rectangle corners, ping-pong the sequences along
  the rectangle edges, paint outer bars with each sequence head, and mirror
  the decoration gadget to the other three corners. Licensed only on perfect
  train replay.

Canonical close: AGI-2 test task 34cfa167.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _comps(inp: Grid, color: int) -> List[List[Tuple[int, int]]]:
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    out: List[List[Tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or inp[r][c] != color:
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
                        and inp[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))
            out.append(cells)
    return out


def _pingpong(seq: List[int], n: int) -> List[int]:
    if n <= 0 or not seq:
        return []
    if len(seq) == 1:
        return seq * n
    out: List[int] = []
    i = 0
    di = 1
    for _ in range(n):
        out.append(seq[i])
        ni = i + di
        if ni < 0 or ni >= len(seq):
            di = -di
            ni = i + di
        i = ni
    return out


def _dist_box(r: int, c: int, box: Tuple[int, int, int, int]) -> int:
    r0, r1, c0, c1 = box
    dr = 0 if r0 <= r <= r1 else (r0 - r if r < r0 else r - r1)
    dc = 0 if c0 <= c <= c1 else (c0 - c if c < c0 else c - c1)
    return dr + dc


def _apply(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    bg = Counter(v for row in inp for v in row).most_common(1)[0][0]
    ones = _comps(inp, 1)
    if len(ones) != 2:
        return None
    boxes = []
    for cells in ones:
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        boxes.append((min(rs), max(rs), min(cs), max(cs)))
    centers = [((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, b) for b in boxes]
    TL = min(centers, key=lambda x: (x[0] + x[1]))[2]
    BR = max(centers, key=lambda x: (x[0] + x[1]))[2]
    Ar0, Ar1, Ac0, Ac1 = TL
    Br0, Br1, Bc0, Bc1 = BR
    gadget = []
    for r in range(h):
        for c in range(w):
            v = inp[r][c]
            if v in (bg, 1):
                continue
            if _dist_box(r, c, TL) <= _dist_box(r, c, BR):
                gadget.append((r, c, v))
    maxc = max([c for r, c, v in gadget if Ar0 <= r <= Ar1] or [Ac1])
    maxr = max([r for r, c, v in gadget if Ac0 <= c <= Ac1] or [Ar1])
    hs = [inp[Ar0][c] for c in range(Ac1 + 1, maxc + 1)]
    vs = [inp[r][Ac0] for r in range(Ar1 + 1, maxr + 1)]
    if not hs or not vs:
        return None
    out = [[bg] * w for _ in range(h)]
    ah, aw = Ar1 - Ar0 + 1, Ac1 - Ac0 + 1
    for r0, c0 in ((Ar0, Ac0), (Ar0, Bc0), (Br0, Ac0), (Br0, Bc0)):
        for dr in range(ah):
            for dc in range(aw):
                rr, cc = r0 + dr, c0 + dc
                if 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = 1
    for r, c, v in gadget:
        out[r][c] = v
    width = Bc0 - Ac1 - 1
    hseq = _pingpong(hs, width)
    for r in list(range(Ar0, Ar1 + 1)) + list(range(Br0, Br1 + 1)):
        for i, col in enumerate(hseq):
            out[r][Ac1 + 1 + i] = col
    height = Br0 - Ar1 - 1
    vseq = _pingpong(vs, height)
    for c in list(range(Ac0, Ac1 + 1)) + list(range(Bc0, Bc1 + 1)):
        for i, col in enumerate(vseq):
            out[Ar1 + 1 + i][c] = col
    bar_h = hs[0]
    for r in (Ar0 - 1, Br1 + 1):
        if 0 <= r < h:
            for c in range(Ac1 + 1, Bc0):
                out[r][c] = bar_h
    bar_v = vs[0]
    for c in (Ac0 - 1, Bc1 + 1):
        if 0 <= c < w:
            for r in range(Ar1 + 1, Br0):
                out[r][c] = bar_v
    mid_c = (Ac1 + Bc0) / 2
    mid_r = (Ar1 + Br0) / 2
    for r, c, v in gadget:
        c2 = int(2 * mid_c - c)
        r2 = int(2 * mid_r - r)
        if 0 <= c2 < w:
            out[r][c2] = v
        if 0 <= r2 < h:
            out[r2][c] = v
        if 0 <= r2 < h and 0 <= c2 < w:
            out[r2][c2] = v
    return out


def make_dual_anchor_pingpong_frame() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _apply(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("dual_anchor_pingpong_frame", make_dual_anchor_pingpong_frame())]


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
            "engine": "s2_dual_anchor_pingpong_frame",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_dual_anchor_pingpong_frame",
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
