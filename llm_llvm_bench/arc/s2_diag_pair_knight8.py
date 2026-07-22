"""S2 diagonal-pair knight-8 (FoT).

Grammar (same_canvas_rewrite):
  Motif color 3. When all motif cells are singleton 4-connected components,
  for every diagonally adjacent pair paint 8 at their shared knight-attack
  intersections (on background). When exactly two 2x2 blocks exist, stamp an
  8-copy of the first block at center1 + (-2*vx, vy) for v = center2-center1,
  and paint a 2-high 8 strip on the near vertical border at rows around
  y1 - vy.

Canonical close: AGI-2 test task 22233c11.
Licensed only on perfect train replay.
"""

from __future__ import annotations

import math
from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _knights(r: int, c: int):
    for dr, dc in (
        (-2, -1),
        (-2, 1),
        (-1, -2),
        (-1, 2),
        (1, -2),
        (1, 2),
        (2, -1),
        (2, 1),
    ):
        yield r + dr, c + dc


def make_diag_pair_knight8() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        bg, mcol, eight = 0, 3, 8
        cells = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == mcol]
        if len(cells) < 2:
            return None
        cellset = set(cells)
        seen = set()
        blobs: List[List[Tuple[int, int]]] = []
        for r, c in cells:
            if (r, c) in seen:
                continue
            q = deque([(r, c)])
            comp: List[Tuple[int, int]] = []
            seen.add((r, c))
            while q:
                x, y = q.popleft()
                comp.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = (x + dx, y + dy)
                    if nxt in cellset and nxt not in seen:
                        seen.add(nxt)
                        q.append(nxt)
            blobs.append(comp)
        out = [list(row) for row in inp]
        painted = False
        singles = [b[0] for b in blobs if len(b) == 1]
        if len(singles) == len(cells):
            for i, (r1, c1) in enumerate(singles):
                for r2, c2 in singles[i + 1 :]:
                    if abs(r1 - r2) == 1 and abs(c1 - c2) == 1:
                        for rr, cc in set(_knights(r1, c1)) & set(_knights(r2, c2)):
                            if 0 <= rr < h and 0 <= cc < w and out[rr][cc] == bg:
                                out[rr][cc] = eight
                                painted = True
            return out if painted else None
        def _solid_square(b: List[Tuple[int, int]]) -> Optional[int]:
            rs = [r for r, _ in b]
            cs = [c for _, c in b]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            side = r1 - r0 + 1
            if c1 - c0 + 1 != side:
                return None
            if len(b) != side * side:
                return None
            return side

        blocks = [(b, _solid_square(b)) for b in blobs]
        blocks = [(b, s) for b, s in blocks if s is not None and s >= 2]
        if len(blocks) != 2 or blocks[0][1] != blocks[1][1]:
            return None
        side = blocks[0][1]

        def center(b: List[Tuple[int, int]]) -> Tuple[float, float]:
            n = len(b)
            return (sum(r for r, _ in b) / n, sum(c for _, c in b) / n)

        # Discovery order — matches train0 geometry.
        (y1, x1), (y2, x2) = center(blocks[0][0]), center(blocks[1][0])
        vy, vx = y2 - y1, x2 - x1
        cy, cx = y1 + (-2 * vx), x1 + vy
        for r, c in blocks[0][0]:
            rr = int(round(r - y1 + cy))
            cc = int(round(c - x1 + cx))
            if 0 <= rr < h and 0 <= cc < w and out[rr][cc] == bg:
                out[rr][cc] = eight
                painted = True
        strip_r0 = max(0, math.floor(y1 - vy))
        border_c = 0 if x2 < x1 else w - 1
        for i in range(side):
            rr = strip_r0 + i
            if 0 <= rr < h and out[rr][border_c] == bg:
                out[rr][border_c] = eight
                painted = True
        return out if painted else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("diag_pair_knight8", make_diag_pair_knight8())]


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
            "engine": "s2_diag_pair_knight8",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_diag_pair_knight8",
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
