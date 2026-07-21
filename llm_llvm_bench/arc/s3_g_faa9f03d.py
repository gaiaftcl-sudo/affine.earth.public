"""FoT engine for eval task faa9f03d.

Grammar family owned here:
  g_faa9f03d (canonical: eval task faa9f03d)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/octotetrahedral-agi · faa9f03d). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_faa9f03d(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


import json
import sys
from copy import deepcopy
from collections import deque


def transform(grid):
    R, C = len(grid), len(grid[0])
    result = deepcopy(grid)
    marked_rows = set()  # rows where a 2-marker was resolved (enables multi-cell H scan)
    marked_cols = set()  # cols where a 2-marker was resolved (enables multi-cell V scan)

    # Step 1: Fill 2-markers iteratively (order: up/down/left/right)
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
                            marked_rows.add(r)
                            marked_cols.add(c)
                            changed = True
                            break

    # Step 2: Handle 4-markers with extension + corrected abandonment
    # Tracks cells placed by extension so they are pre-locked in gap-fill
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

                    # Extension: fill marker then extend away from path cell to edge
                    result[r][c] = path_color
                    extension_cells.add((r, c))
                    er, ec = r + ext_dr, c + ext_dc
                    while 0 <= er < R and 0 <= ec < C:
                        dist = max(abs(er - r), abs(ec - c))
                        # Fix 4': for horizontal extensions only, skip non-zero non-path cells beyond dist=1
                        if ext_dc != 0 and result[er][ec] != 0 and result[er][ec] != path_color and dist > 1:
                            er += ext_dr
                            ec += ext_dc
                            continue
                        result[er][ec] = path_color
                        extension_cells.add((er, ec))
                        er += ext_dr
                        ec += ext_dc

                    # Abandonment: walk in path direction, skip at most 1 consecutive zero
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

                    # BFS from zeroed cells to remove connected branches (excluding path/marker)
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

    # Step 3: Gap-fill with incremental updates and lock-on-first-change
    # Extension cells are pre-locked (4-marker placed them definitively)
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
            if axis == 'H' and r2 != gap_r:
                return True
            if axis == 'V' and c2 != gap_c:
                return True
        return False

    def find_nearest_nonzero(r, c, dr, dc):
        """Scan in (dr,dc) direction for the nearest non-zero, non-marker cell.
        Returns None if an abandoned cell (non-zero in original, zero now) blocks the path."""
        nr, nc = r + dr, c + dc
        while 0 <= nr < R and 0 <= nc < C:
            if result[nr][nc] not in (0, 2, 4):
                return (nr, nc)
            if grid[nr][nc] != 0 and result[nr][nc] == 0:
                return None  # abandoned cell — invalid scan path
            nr += dr
            nc += dc
        return None

    def min_run_count(r, c, dr, dc, color):
        """Count consecutive cells of color starting one step in (dr,dc)."""
        count = 0
        nr, nc = r + dr, c + dc
        while 0 <= nr < R and 0 <= nc < C and result[nr][nc] == color:
            count += 1
            nr += dr
            nc += dc
        return count

    for _ in range(25):
        changed = False
        for r in range(R):
            for c in range(C):
                if (r, c) in locked:
                    continue
                cur = result[r][c]
                if cur in (2, 4):
                    continue

                candidates = []  # (color, is_L_shaped, axis)
                for (dr1, dc1), (dr2, dc2), axis in [
                    ((0, -1), (0, 1), 'H'),
                    ((-1, 0), (1, 0), 'V'),
                ]:
                    # Use nearest-nonzero scan for marked rows/cols (multi-cell)
                    if axis == 'H' and r in marked_rows:
                        pos1 = find_nearest_nonzero(r, c, 0, -1)
                        pos2 = find_nearest_nonzero(r, c, 0, 1)
                    elif axis == 'V' and c in marked_cols:
                        pos1 = find_nearest_nonzero(r, c, -1, 0)
                        pos2 = find_nearest_nonzero(r, c, 1, 0)
                    else:
                        r1i, c1i = r + dr1, c + dc1
                        r2i, c2i = r + dr2, c + dc2
                        pos1 = (r1i, c1i) if 0 <= r1i < R and 0 <= c1i < C else None
                        pos2 = (r2i, c2i) if 0 <= r2i < R and 0 <= c2i < C else None

                    if pos1 is None or pos2 is None:
                        continue
                    r1, c1 = pos1
                    r2, c2 = pos2

                    v1, v2 = result[r1][c1], result[r2][c2]
                    if v1 != v2 or v1 in (0, 2, 4):
                        continue
                    Y = v1

                    comp1 = get_component(r1, c1, Y, r, c)
                    if (r2, c2) in comp1:
                        continue  # endpoints connected — not a bridging gap

                    comp2 = get_component(r2, c2, Y, r, c)
                    comp1_L = component_is_L(comp1, r, c, axis)
                    comp2_L = component_is_L(comp2, r, c, axis)

                    # Determine if multi-cell scan (at least one endpoint beyond dist=1)
                    dist1 = abs(r1 - r) + abs(c1 - c)
                    dist2 = abs(r2 - r) + abs(c2 - c)
                    any_multicell = (axis == 'H' and r in marked_rows) or \
                                    (axis == 'V' and c in marked_cols)
                    any_multicell = any_multicell and (dist1 > 1 or dist2 > 1)

                    if any_multicell:
                        # Asymmetric rule: exactly one near (dist=1) + one far (dist>1)
                        # => l_shaped iff near-comp is L and far-comp is NOT L
                        # Both far => l_shaped = False (never fill)
                        if dist1 == 1 and dist2 > 1:
                            l_shaped = comp1_L and not comp2_L
                        elif dist2 == 1 and dist1 > 1:
                            l_shaped = comp2_L and not comp1_L
                        else:
                            l_shaped = False
                        if not l_shaped:
                            continue
                    else:
                        l_shaped = comp1_L or comp2_L
                        # Non-zero cells: only allow if L-shaped
                        if cur != 0 and not l_shaped:
                            continue
                        # Fix 5: for original non-zero cells, block extension-cell sandwiches
                        if (cur != 0 and grid[r][c] != 0 and result[r][c] == grid[r][c] and
                                (r1, c1) in extension_cells and (r2, c2) in extension_cells):
                            continue

                    candidates.append((Y, l_shaped, axis))

                if not candidates:
                    continue

                # L-shaped non-cur candidates win; otherwise min of all candidates
                l_noncur = [(Y, ax) for Y, l, ax in candidates if l and Y != cur]
                if l_noncur:
                    if len(l_noncur) > 1:
                        # Fix 2: tiebreak by min_run (prefer larger; ties broken by smaller color)
                        best_key, winner = None, None
                        for Y_cand, ax_cand in l_noncur:
                            if ax_cand == 'H':
                                run = min(min_run_count(r, c, 0, -1, Y_cand),
                                          min_run_count(r, c, 0, 1, Y_cand))
                            else:
                                run = min(min_run_count(r, c, -1, 0, Y_cand),
                                          min_run_count(r, c, 1, 0, Y_cand))
                            key = (run, -Y_cand)
                            if best_key is None or key > best_key:
                                best_key, winner = key, Y_cand
                    else:
                        winner = l_noncur[0][0]
                else:
                    winner = min(Y for Y, _, _ in candidates)

                if winner != cur:
                    result[r][c] = winner
                    locked.add((r, c))
                    changed = True

        if not changed:
            break

    return result



def _solve(grid: Grid):
    return transform(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_faa9f03d", g_faa9f03d)]


def exact_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    out: List[Tuple[str, Transform]] = []
    for name, transform in named_candidates():
        if all(transform(ex["input"]) == ex["output"] for ex in train):
            out.append((name, transform))
    return out


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    train = task.get("train", [])
    exact = exact_candidates(train)
    if not exact:
        return {
            "engine": "s3_g_faa9f03d",
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
        "engine": "s3_g_faa9f03d",
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
