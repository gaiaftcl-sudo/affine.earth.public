"""Batch FoT engine for eval task 9385bd28.

Grammar family owned here:
  g_9385bd28 (canonical: eval task 9385bd28)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 9385bd28). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_9385bd28(grid: Grid) -> Optional[Grid]:
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
ARC-AGI puzzle 9385bd28 solver.

Pattern: Pairs of L-shaped triominoes define rectangles. A legend maps
object colors to fill colors. Each pair's bounding box is filled. Fills
are layered by legend position (topmost legend entry = highest priority).
Non-legend L-pairs have their cells and missing corners protected.
If a non-legend L-pair's bbox is fully inside an active fill, the whole
bbox acts as a transparent hole.
"""

import json
from collections import defaultdict


def transform(grid):
    H = len(grid)
    W = len(grid[0])

    counts = defaultdict(int)
    for row in grid:
        for v in row:
            counts[v] += 1
    bg = max(counts, key=counts.get)

    color_pos = defaultdict(list)
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg:
                color_pos[grid[r][c]].append((r, c))

    def find_clusters(positions):
        pos_set = set(positions)
        visited = set()
        clusters = []
        for p in positions:
            if p in visited:
                continue
            cluster = []
            stack = [p]
            while stack:
                cur = stack.pop()
                if cur in visited:
                    continue
                visited.add(cur)
                cluster.append(cur)
                r, c = cur
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nb = (r + dr, c + dc)
                    if nb in pos_set and nb not in visited:
                        stack.append(nb)
            clusters.append(sorted(cluster))
        return clusters

    def get_missing_corner(cluster):
        rs = [r for r, c in cluster]
        cs = [c for r, c in cluster]
        s = set(cluster)
        for r in range(min(rs), max(rs) + 1):
            for c in range(min(cs), max(cs) + 1):
                if (r, c) not in s:
                    return (r, c)
        return None

    def bbox_of(positions):
        rs = [r for r, c in positions]
        cs = [c for r, c in positions]
        return (min(rs), max(rs), min(cs), max(cs))

    def bbox_contains(outer, inner):
        return (outer[0] <= inner[0] and inner[1] <= outer[1] and
                outer[2] <= inner[2] and inner[3] <= outer[3])

    def cell_in_bbox(r, c, bbox):
        return bbox[0] <= r <= bbox[1] and bbox[2] <= c <= bbox[3]

    # Classify clusters
    l_pairs = {}
    legend_candidates = []
    for color in sorted(color_pos.keys()):
        clusters = find_clusters(color_pos[color])
        size3 = [c for c in clusters if len(c) == 3]
        small = [c for c in clusters if len(c) <= 2]
        if len(size3) == 2:
            l_pairs[color] = (size3[0], size3[1])
        for cl in small:
            for pos in cl:
                legend_candidates.append((pos, color))

    # Parse legend (horizontal adjacent pairs, left=source, right=fill)
    legend_positions = {pos: color for pos, color in legend_candidates}
    legend_mapping = {}
    legend_rows = {}
    used = set()
    for (r, c), color in sorted(legend_candidates):
        if (r, c) in used:
            continue
        right = (r, c + 1)
        if right in legend_positions and right not in used:
            legend_mapping[color] = legend_positions[right]
            legend_rows[color] = r
            used.add((r, c))
            used.add(right)

    legend_cell_set = {pos for pos, _ in legend_candidates}

    # Active L-pair fills (source has L-pair and fill != 0)
    active_fills = {}
    for src, fill in legend_mapping.items():
        if fill == 0:
            continue
        if src in l_pairs:
            active_fills[src] = fill

    # Non-L-pair fills (source in legend, no L-pair, fill != 0)
    non_lpair_fills = {}
    for src, fill in legend_mapping.items():
        if fill == 0 or src in l_pairs:
            continue
        non_legend = [p for p in color_pos.get(src, []) if p not in legend_cell_set]
        if non_legend:
            non_lpair_fills[src] = (fill, non_legend)

    # Compute bboxes and fill colors for all fills
    bboxes = {}
    fill_colors = {}
    for color in active_fills:
        L1, L2 = l_pairs[color]
        bboxes[color] = bbox_of(L1 + L2)
        fill_colors[color] = active_fills[color]
    for color in non_lpair_fills:
        fill, positions = non_lpair_fills[color]
        bboxes[color] = bbox_of(positions)
        fill_colors[color] = fill

    # Non-legend L-pairs
    non_legend_colors = set()
    non_legend_lpair_bboxes = {}
    for color in l_pairs:
        if color not in legend_mapping:
            non_legend_colors.add(color)
            L1, L2 = l_pairs[color]
            non_legend_lpair_bboxes[color] = bbox_of(L1 + L2)

    # Holes: non-legend L-pair bbox fully inside a fill's bbox
    holes_per_fill = defaultdict(list)
    for nl_color, nl_bbox in non_legend_lpair_bboxes.items():
        for fill_src, fill_bbox in bboxes.items():
            if bbox_contains(fill_bbox, nl_bbox):
                holes_per_fill[fill_src].append(nl_bbox)

    # Protected cells: non-legend L-shape cells + their missing corners
    protected_cells = set()
    for color in non_legend_colors:
        L1, L2 = l_pairs[color]
        for cell in L1 + L2:
            protected_cells.add(cell)
        for cl in (L1, L2):
            mc = get_missing_corner(cl)
            if mc:
                protected_cells.add(mc)

    # Sort by legend row descending (bottom = lowest priority, top = highest)
    sorted_fills = sorted(
        fill_colors.keys(),
        key=lambda c: legend_rows.get(c, 0),
        reverse=True,
    )

    result = [row[:] for row in grid]

    # Apply fills in priority order
    for color in sorted_fills:
        fc = fill_colors[color]
        r0, r1, c0, c1 = bboxes[color]
        holes = holes_per_fill.get(color, [])
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if any(cell_in_bbox(r, c, h) for h in holes):
                    continue
                if (r, c) in protected_cells:
                    continue
                result[r][c] = fc

    # Restore active L-shape cells on top
    for color in active_fills:
        L1, L2 = l_pairs[color]
        for r, c in L1 + L2:
            result[r][c] = color

    return result



def _solve(grid: Grid):
    return transform(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_9385bd28", g_9385bd28)]


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
            "engine": "s3_g_9385bd28",
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
        "engine": "s3_g_9385bd28",
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
    "g_9385bd28",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
