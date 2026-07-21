"""Batch FoT engine for eval task faa9f03d.

Grammar family owned here:
  g_faa9f03d (canonical: eval task faa9f03d)
    C4: licensed only on perfect train replay.

Path-fix language game: 2-marker fill, 4-marker extend/abandon,
gap-fill, then XOR-L long-gap / V-over-H / foreign-restore heals.
Never submits to Kaggle.
"""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _get_comp(grid: Grid, r0: int, c0: int, color: int) -> set:
    R, C = len(grid), len(grid[0])
    vis = set()
    q = deque([(r0, c0)])
    vis.add((r0, c0))
    while q:
        r, c = q.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and (nr, nc) not in vis and grid[nr][nc] == color:
                vis.add((nr, nc))
                q.append((nr, nc))
    return vis


def _base_transform(grid: Grid) -> Grid:
    R, C = len(grid), len(grid[0])
    result = deepcopy(grid)

    changed = True
    while changed:
        changed = False
        for r in range(R):
            for c in range(C):
                if result[r][c] == 2:
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < R and 0 <= nc < C and result[nr][nc] not in (0, 2, 4):
                            result[r][c] = result[nr][nc]
                            changed = True
                            break

    extension_cells = set()
    for r in range(R):
        for c in range(C):
            if grid[r][c] != 4:
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < R and 0 <= nc < C and result[nr][nc] not in (0, 2, 4):
                    path_color = result[nr][nc]
                    path_r, path_c = nr, nc
                    ext_dr, ext_dc = -dr, -dc
                    result[r][c] = path_color
                    extension_cells.add((r, c))
                    er, ec = r + ext_dr, c + ext_dc
                    while 0 <= er < R and 0 <= ec < C:
                        result[er][ec] = path_color
                        extension_cells.add((er, ec))
                        er += ext_dr
                        ec += ext_dc
                    zeroed = []
                    ar, ac = r + 2 * dr, c + 2 * dc
                    zero_run = 0
                    while 0 <= ar < R and 0 <= ac < C:
                        if result[ar][ac] == path_color:
                            result[ar][ac] = 0
                            zeroed.append((ar, ac))
                            zero_run = 0
                        elif result[ar][ac] == 0:
                            zero_run += 1
                            if zero_run > 1:
                                break
                        else:
                            break
                        ar += dr
                        ac += dc
                    q2 = deque(zeroed)
                    visited = set(zeroed)
                    while q2:
                        br, bc = q2.popleft()
                        for dr2, dc2 in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            nr2, nc2 = br + dr2, bc + dc2
                            if (nr2, nc2) in {(path_r, path_c), (r, c)} | visited:
                                continue
                            if 0 <= nr2 < R and 0 <= nc2 < C and result[nr2][nc2] == path_color:
                                result[nr2][nc2] = 0
                                visited.add((nr2, nc2))
                                q2.append((nr2, nc2))
                    break

    locked = set(extension_cells)

    def get_component(r0, c0, color, gap_r, gap_c):
        vis = set()
        q = deque([(r0, c0)])
        vis.add((r0, c0))
        while q:
            r2, c2 = q.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r2 + dr, c2 + dc
                if (nr, nc) == (gap_r, gap_c) or (nr, nc) in vis:
                    continue
                if 0 <= nr < R and 0 <= nc < C and result[nr][nc] == color:
                    vis.add((nr, nc))
                    q.append((nr, nc))
        return vis

    def component_is_L(comp, gap_r, gap_c, axis):
        for r2, c2 in comp:
            if axis == "H" and r2 != gap_r:
                return True
            if axis == "V" and c2 != gap_c:
                return True
        return False

    def has_other_neighbor(r2, c2, color, exc_r, exc_c):
        if (r2, c2) in extension_cells:
            return True
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r2 + dr, c2 + dc
            if (nr, nc) != (exc_r, exc_c) and 0 <= nr < R and 0 <= nc < C and result[nr][nc] == color:
                return True
        return False

    for _ in range(25):
        changed = False
        for r in range(R):
            for c in range(C):
                if (r, c) in locked:
                    continue
                cur = result[r][c]
                if cur in (2, 4):
                    continue
                candidates = []
                for (r1, c1), (r2, c2), axis in [
                    ((r, c - 1), (r, c + 1), "H"),
                    ((r - 1, c), (r + 1, c), "V"),
                ]:
                    if not (0 <= r1 < R and 0 <= c1 < C and 0 <= r2 < R and 0 <= c2 < C):
                        continue
                    v1, v2 = result[r1][c1], result[r2][c2]
                    if v1 != v2 or v1 in (0, 2, 4):
                        continue
                    Y = v1
                    comp1 = get_component(r1, c1, Y, r, c)
                    if (r2, c2) in comp1:
                        continue
                    if cur != 0:
                        if not (
                            has_other_neighbor(r1, c1, Y, r, c)
                            and has_other_neighbor(r2, c2, Y, r, c)
                        ):
                            continue
                    comp2 = get_component(r2, c2, Y, r, c)
                    l_shaped = component_is_L(comp1, r, c, axis) or component_is_L(
                        comp2, r, c, axis
                    )
                    candidates.append((Y, l_shaped))
                if not candidates:
                    continue
                l_noncur = [Y for Y, l in candidates if l and Y != cur]
                winner = min(l_noncur) if l_noncur else min(Y for Y, _ in candidates)
                if winner != cur:
                    result[r][c] = winner
                    locked.add((r, c))
                    changed = True
        if not changed:
            break
    return result


def g_faa9f03d(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        result = _base_transform(grid)
        R, C = len(result), len(result[0])
        inp = grid

        for r in range(R):
            c = 0
            while c < C:
                if result[r][c] != 0:
                    c += 1
                    continue
                start = c
                while c < C and result[r][c] == 0:
                    c += 1
                end = c - 1
                if start == 0 or end == C - 1:
                    continue
                left, right = result[r][start - 1], result[r][end + 1]
                if left != right or left in (0, 2, 4):
                    continue
                c1 = _get_comp(result, r, start - 1, left)
                if (r, end + 1) in c1:
                    continue
                c2 = _get_comp(result, r, end + 1, left)
                l1 = any(rr != r for rr, _ in c1)
                l2 = any(rr != r for rr, _ in c2)
                if l1 != l2:
                    for cc in range(start, end + 1):
                        result[r][cc] = left

        for r in range(1, R - 1):
            for c in range(1, C - 1):
                if inp[r][c] != 0:
                    continue
                V = (
                    result[r - 1][c]
                    if result[r - 1][c] == result[r + 1][c] and result[r - 1][c] not in (0, 2, 4)
                    else None
                )
                H = (
                    result[r][c - 1]
                    if result[r][c - 1] == result[r][c + 1] and result[r][c - 1] not in (0, 2, 4)
                    else None
                )
                if not (V and H and V != H):
                    continue
                vc = _get_comp(result, r - 1, c, V)
                hc = _get_comp(result, r, c - 1, H)
                vL = any(cc != c for _, cc in vc)
                hL = any(rr != r for rr, _ in hc)
                if vL and not hL:
                    result[r][c] = V
                elif vL and hL:
                    vcol = sum(1 for rr in range(R) if result[rr][c] == V)
                    hrow = sum(1 for cc in range(C) if result[r][cc] == H)
                    if vcol > hrow:
                        result[r][c] = V

        for r in range(1, R - 1):
            for c in range(C):
                cur = result[r][c]
                if inp[r][c] != cur or cur in (0, 2, 4):
                    continue
                V = result[r - 1][c]
                if not (V == result[r + 1][c] and V not in (0, 2, 4) and V != cur):
                    continue
                H = None
                if (
                    c > 0
                    and c + 1 < C
                    and result[r][c - 1] == result[r][c + 1]
                    and result[r][c - 1] not in (0, 2, 4)
                ):
                    H = result[r][c - 1]
                if H is None or H == cur:
                    result[r][c] = V

        for r in range(R):
            for c in range(1, C - 1):
                cur = result[r][c]
                if cur in (0, 2, 4) or inp[r][c] != cur:
                    continue
                H = result[r][c - 1]
                if H != result[r][c + 1] or H in (0, 2, 4) or H == cur:
                    continue
                if r > 0 and r + 1 < R and result[r - 1][c] == result[r + 1][c] == cur:
                    continue
                result[r][c] = H

        for r in range(R):
            for c4 in range(C):
                if inp[r][c4] != 4:
                    continue
                pc = result[r][c4]
                if pc in (0, 2, 4):
                    continue
                left = sum(1 for c in range(c4) if result[r][c] == pc)
                right = sum(1 for c in range(c4 + 1, C) if result[r][c] == pc)
                cells = list(range(c4 + 1, C)) if right >= left else list(range(c4 - 1, -1, -1))
                step = 1 if right >= left else -1
                foreign_pos = None
                for c in cells:
                    f = inp[r][c]
                    if f not in (0, 2, 4) and f != pc and abs(c - c4) > 1:
                        foreign_pos = c
                        break
                if foreign_pos is None:
                    continue
                result[r][foreign_pos] = inp[r][foreign_pos]
                c = foreign_pos + step
                while 0 <= c < C:
                    if result[r][c] == 0:
                        result[r][c] = pc
                    c += step
    except Exception:
        return None
    if not result or not result[0]:
        return None
    return result


def named_candidates() -> List[Tuple[str, Transform]]:
    return [("g_faa9f03d", g_faa9f03d)]


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
            "engine": "s2_g_faa9f03d",
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
        "engine": "s2_g_faa9f03d",
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
    "g_faa9f03d",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
