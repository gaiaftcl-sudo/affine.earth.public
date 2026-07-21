"""Batch FoT engine for eval task a25697e4.

Grammar family owned here:
  g_a25697e4 (canonical: eval task a25697e4)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · a25697e4). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_a25697e4(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


"""
ARC-AGI solver for task a25697e4.

Pattern: There are colored shapes on a background. Each "puzzle group" has:
- An "anchor" = a color with 2 disconnected components forming a shape with gaps
- A "pair" = two adjacent shapes of different colors

The pair gets rotated/reflected as a rigid body and placed so one shape fills
the anchor's gaps and the other extends outward. For reflections (chirality-
reversing transforms), the pair colors are swapped.

Multiple independent puzzle groups may exist in one grid.
"""
import json
from typing import List
from collections import Counter
from itertools import combinations


def solve(grid: List[List[int]]) -> List[List[int]]:
    H, W = len(grid), len(grid[0])

    color_counts = Counter(grid[r][c] for r in range(H) for c in range(W))
    bg = color_counts.most_common(1)[0][0]

    visited = [[False] * W for _ in range(H)]
    components: list[tuple[int, list[tuple[int, int]]]] = []

    def bfs(r, c, color):
        stack = [(r, c)]
        cells = []
        while stack:
            r2, c2 = stack.pop()
            if 0 <= r2 < H and 0 <= c2 < W and not visited[r2][c2] and grid[r2][c2] == color:
                visited[r2][c2] = True
                cells.append((r2, c2))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    stack.append((r2 + dr, c2 + dc))
        return cells

    for r in range(H):
        for c in range(W):
            if not visited[r][c] and grid[r][c] != bg:
                cells = bfs(r, c, grid[r][c])
                if cells:
                    components.append((grid[r][c], cells))

    comp_sets = [set(cells) for _, cells in components]
    adj_pairs = []
    for i in range(len(components)):
        for j in range(i + 1, len(components)):
            if components[i][0] == components[j][0]:
                continue
            found = False
            for r, c in components[i][1]:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    if (r + dr, c + dc) in comp_sets[j]:
                        adj_pairs.append((i, j))
                        found = True
                        break
                if found:
                    break

    def apply_transform(cells, tid):
        rs = [r for r, c, _ in cells]
        cs = [c for r, c, _ in cells]
        max_r, max_c = max(rs), max(cs)
        fns = {
            0: lambda r, c: (r, c),
            1: lambda r, c: (c, max_r - r),
            2: lambda r, c: (max_r - r, max_c - c),
            3: lambda r, c: (max_c - c, r),
            4: lambda r, c: (r, max_c - c),
            5: lambda r, c: (max_r - r, c),
            6: lambda r, c: (c, r),
            7: lambda r, c: (max_c - c, max_r - r),
        }
        fn = fns[tid]
        result = [(fn(r, c)[0], fn(r, c)[1], color) for r, c, color in cells]
        mr = min(r for r, c, _ in result)
        mc = min(c for r, c, _ in result)
        return [(r - mr, c - mc, color) for r, c, color in result]

    def try_place(anchor_indices, pair_indices, output):
        anchor_cells = set()
        for ci in anchor_indices:
            anchor_cells.update(components[ci][1])

        a_rmin = min(r for r, c in anchor_cells)
        a_rmax = max(r for r, c in anchor_cells)
        a_cmin = min(c for r, c in anchor_cells)
        a_cmax = max(c for r, c in anchor_cells)

        gaps = set()
        for r in range(a_rmin, a_rmax + 1):
            for c in range(a_cmin, a_cmax + 1):
                if (r, c) not in anchor_cells:
                    gaps.add((r, c))

        if not gaps:
            return False

        pair_cells = []
        pair_colors = []
        for ci in pair_indices:
            color = components[ci][0]
            if color not in pair_colors:
                pair_colors.append(color)
            for r, c in components[ci][1]:
                pair_cells.append((r, c, color))

        if len(pair_colors) != 2:
            return False

        pr = min(r for r, c, _ in pair_cells)
        pc = min(c for r, c, _ in pair_cells)
        pair_rel = [(r - pr, c - pc, col) for r, c, col in pair_cells]
        pc1, pc2 = pair_colors

        for tid in range(8):
            is_refl = tid >= 4
            if is_refl:
                variant = [(r, c, pc2 if col == pc1 else pc1) for r, c, col in pair_rel]
            else:
                variant = pair_rel
            transformed = apply_transform(variant, tid)

            for fc in pair_colors:
                filler = [(r, c) for r, c, col in transformed if col == fc]
                if len(filler) != len(gaps):
                    continue

                gs = sorted(gaps)
                fs = sorted(filler)
                dr = gs[0][0] - fs[0][0]
                dc = gs[0][1] - fs[0][1]

                if {(r + dr, c + dc) for r, c in filler} != gaps:
                    continue

                placed = [(r + dr, c + dc, col) for r, c, col in transformed]

                if any(r < 0 or r >= H or c < 0 or c >= W for r, c, _ in placed):
                    continue
                if {(r, c) for r, c, _ in placed} & anchor_cells:
                    continue

                for ci in pair_indices:
                    for r, c in components[ci][1]:
                        output[r][c] = bg
                for r, c, col in placed:
                    output[r][c] = col
                return True

        return False

    output = [row[:] for row in grid]
    used = set()

    for pi, pj in adj_pairs:
        if pi in used or pj in used:
            continue

        color_groups = {}
        for ci, (color, cells) in enumerate(components):
            if ci in {pi, pj} or ci in used:
                continue
            color_groups.setdefault(color, []).append(ci)

        found = False
        for acolor, indices in color_groups.items():
            if len(indices) < 2:
                continue
            for apair in combinations(indices, 2):
                ac = set()
                for ai in apair:
                    ac.update(components[ai][1])
                ar = [r for r, c in ac]
                acols = [c for r, c in ac]
                bbox = (max(ar) - min(ar) + 1) * (max(acols) - min(acols) + 1)
                if bbox > 300:
                    continue
                if try_place(list(apair), [pi, pj], output):
                    used.update([pi, pj])
                    used.update(apair)
                    found = True
                    break
            if found:
                break

    return output


if __name__ == "__main__":
    with open("/Users/evanpieser/arc-puzzle-catalog/dataset/tasks/a25697e4.json") as f:
        task = json.load(f)

    ok = True
    for i, ex in enumerate(task["train"]):
        result = solve(ex["input"])
        if result == ex["output"]:
            print(f"Train {i}: PASS")
        else:
            print(f"Train {i}: FAIL")
            ok = False

    for i, ex in enumerate(task["test"]):
        result = solve(ex["input"])
        print(f"Test {i}: solved ({len(result)}x{len(result[0])})")

    if ok:
        print("\nALL PASS")



def _solve(grid: Grid):
    return solve(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_a25697e4", g_a25697e4)]


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
            "engine": "s3_g_a25697e4",
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
        "engine": "s3_g_a25697e4",
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
    "g_a25697e4",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
