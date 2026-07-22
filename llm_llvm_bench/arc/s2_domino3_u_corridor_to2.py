"""S2 domino-3 U-corridor to 2 (FoT).

Grammar (same_canvas_rewrite):
  Exactly one 4-connected component of color 3 and one of color 2 (dominos).
  Connect them with a 3-painted U-path on zeros:
    - If their column bands overlap (and rows do not): use a vertical corridor
      at the rightmost feasible column.
    - Otherwise: use a horizontal corridor on the row in the open band between
      their row ranges that is closest to the facing edge of the upper block.
  Endpoints are cells of each domino that admit such a clear U.

Canonical close: AGI-2 test task 2dd70a9a.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _comps(g: Grid, col: int) -> List[List[Tuple[int, int]]]:
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    out: List[List[Tuple[int, int]]] = []
    for i in range(h):
        for j in range(w):
            if seen[i][j] or g[i][j] != col:
                continue
            q = deque([(i, j)])
            seen[i][j] = True
            cells: List[Tuple[int, int]] = []
            while q:
                r, c = q.popleft()
                cells.append((r, c))
                for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
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


def make_domino3_u_corridor_to2(a: int = 3, b: int = 2) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        As, Bs = _comps(inp, a), _comps(inp, b)
        if len(As) != 1 or len(Bs) != 1:
            return None
        A, B = As[0], Bs[0]
        ars = [r for r, _ in A]
        acs = [c for _, c in A]
        brs = [r for r, _ in B]
        bcs = [c for _, c in B]
        ar0, ar1, ac0, ac1 = min(ars), max(ars), min(acs), max(acs)
        br0, br1, bc0, bc1 = min(brs), max(brs), min(bcs), max(bcs)

        def h_ok(r: int, c0: int, c1: int) -> bool:
            if c0 > c1:
                c0, c1 = c1, c0
            return all(inp[r][c] in (0, a, b) for c in range(c0, c1 + 1))

        def v_ok(c: int, r0: int, r1: int) -> bool:
            if r0 > r1:
                r0, r1 = r1, r0
            return all(inp[r][c] in (0, a, b) for r in range(r0, r1 + 1))

        def apply_h(rA: int, cA: int, rB: int, cB: int, r: int) -> Grid:
            out = [row[:] for row in inp]
            for rr in range(min(rA, r), max(rA, r) + 1):
                if out[rr][cA] == 0:
                    out[rr][cA] = a
            for cc in range(min(cA, cB), max(cA, cB) + 1):
                if out[r][cc] == 0:
                    out[r][cc] = a
            for rr in range(min(rB, r), max(rB, r) + 1):
                if out[rr][cB] == 0:
                    out[rr][cB] = a
            return out

        def apply_v(rA: int, cA: int, rB: int, cB: int, c: int) -> Grid:
            out = [row[:] for row in inp]
            for cc in range(min(cA, c), max(cA, c) + 1):
                if out[rA][cc] == 0:
                    out[rA][cc] = a
            for rr in range(min(rA, rB), max(rA, rB) + 1):
                if out[rr][c] == 0:
                    out[rr][c] = a
            for cc in range(min(cB, c), max(cB, c) + 1):
                if out[rB][cc] == 0:
                    out[rB][cc] = a
            return out

        share_col = not (ac1 < bc0 or bc1 < ac0)
        share_row = not (ar1 < br0 or br1 < ar0)

        if share_col and not share_row:
            best = None
            for rA, cA in A:
                for rB, cB in B:
                    for c in range(max(ac1, bc1) + 1, w):
                        if h_ok(rA, cA, c) and v_ok(c, rA, rB) and h_ok(rB, c, cB):
                            if best is None or c > best[0]:
                                best = (c, rA, cA, rB, cB)
            if best is None:
                for rA, cA in A:
                    for rB, cB in B:
                        for c in range(w):
                            if h_ok(rA, cA, c) and v_ok(c, rA, rB) and h_ok(rB, c, cB):
                                if best is None or c > best[0]:
                                    best = (c, rA, cA, rB, cB)
            if best is None:
                return None
            c, rA, cA, rB, cB = best
            return apply_v(rA, cA, rB, cB, c)

        if ar1 < br0:
            lo, hi = ar1 + 1, br0 - 1
            face = ar1 + 1
        elif br1 < ar0:
            lo, hi = br1 + 1, ar0 - 1
            face = br1 + 1
        else:
            return None

        best_h = None
        for rA, cA in A:
            for rB, cB in B:
                for r in range(max(0, lo), min(h, hi + 1)):
                    if v_ok(cA, rA, r) and h_ok(r, cA, cB) and v_ok(cB, r, rB):
                        score = (abs(r - face), r)
                        if best_h is None or score < best_h[0]:
                            best_h = (score, r, rA, cA, rB, cB)
        if best_h is None:
            return None
        _, r, rA, cA, rB, cB = best_h
        return apply_h(rA, cA, rB, cB, r)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("domino3_u_corridor_to2", make_domino3_u_corridor_to2())]


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
            "engine": "s2_domino3_u_corridor_to2",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_domino3_u_corridor_to2",
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
