"""S1 canvas-hole sprite fill language game (FoT).

Grammar family owned here:
  canvas_hole_sprite_fill (canonical: eval task 67e490f4)
    S1: majority color = background; largest non-bg component = canvas.
    S2: output crop = canvas bbox; canvas cells kept; bg cells are holes.
    S3: each non-canvas sprite is a 4-connected same-color component; its
        mask is compared to hole masks under rotation + reflection.
    S4: each hole fills with the majority sprite color for that mask class.
    C4: exact filled crop licensed by full train replay.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Mask = frozenset[Tuple[int, int]]


def _majority(grid: Grid) -> int:
    return Counter(cell for row in grid for cell in row).most_common(1)[0][0]


def _components(grid: Grid, match: Callable[[int], bool]) -> List[Dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen = [[False] * width for _ in range(height)]
    comps: List[Dict[str, Any]] = []
    for r in range(height):
        for c in range(width):
            if seen[r][c] or not match(grid[r][c]):
                continue
            color = grid[r][c]
            queue = deque([(r, c)])
            seen[r][c] = True
            cells: List[Tuple[int, int]] = []
            while queue:
                y, x = queue.popleft()
                cells.append((y, x))
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if (
                        0 <= ny < height
                        and 0 <= nx < width
                        and not seen[ny][nx]
                        and grid[ny][nx] == color
                    ):
                        seen[ny][nx] = True
                        queue.append((ny, nx))
            rows = [y for y, _ in cells]
            cols = [x for _, x in cells]
            r0, c0 = min(rows), min(cols)
            mask: Mask = frozenset((y - r0, x - c0) for y, x in cells)
            comps.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": (r0, min(cols), max(rows), max(cols)),
                    "mask": mask,
                    "n": len(cells),
                }
            )
    return comps


def _normalize_mask(mask: Mask) -> Mask:
    """Canonical mask among 4 rotations × horizontal mirrors."""

    def rot90(m: Mask) -> Mask:
        if not m:
            return m
        max_r = max(r for r, _ in m)
        raw = {(c, max_r - r) for r, c in m}
        r0 = min(r for r, _ in raw)
        c0 = min(c for _, c in raw)
        return frozenset((r - r0, c - c0) for r, c in raw)

    def mirror_h(m: Mask) -> Mask:
        if not m:
            return m
        max_c = max(c for _, c in m)
        raw = {(r, max_c - c) for r, c in m}
        r0 = min(r for r, _ in raw)
        c0 = min(c for _, c in raw)
        return frozenset((r - r0, c - c0) for r, c in raw)

    variants: List[Mask] = [mask]
    current = mask
    for _ in range(3):
        current = rot90(current)
        variants.append(current)
    variants.extend(mirror_h(v) for v in list(variants))
    return min(variants, key=lambda v: tuple(sorted(v)))


def canvas_hole_sprite_fill(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    bg = _majority(grid)
    comps = _components(grid, lambda color: color != bg)
    if not comps:
        return None
    canvas = max(comps, key=lambda item: item["n"])
    r0, c0, r1, c1 = canvas["bbox"]
    height, width = r1 - r0 + 1, c1 - c0 + 1
    crop: Grid = [[bg] * width for _ in range(height)]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if grid[r][c] == canvas["color"]:
                crop[r - r0][c - c0] = canvas["color"]

    holes = _components(crop, lambda color: color == bg)
    if not holes:
        return crop

    votes: Dict[Mask, Counter] = defaultdict(Counter)
    for sprite in comps:
        if sprite["color"] == canvas["color"]:
            continue
        votes[_normalize_mask(sprite["mask"])][sprite["color"]] += 1
    if not votes:
        return None

    out = [list(row) for row in crop]
    for hole in holes:
        canon = _normalize_mask(hole["mask"])
        if canon not in votes:
            return None
        fill = votes[canon].most_common(1)[0][0]
        for r, c in hole["cells"]:
            out[r][c] = fill
    if any(cell == bg for row in out for cell in row):
        return None
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("canvas_hole_sprite_fill", canvas_hole_sprite_fill)]


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
            "engine": "s1_canvas_hole_sprite_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_canvas_hole_sprite_fill",
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
    "canvas_hole_sprite_fill",
    "exact_candidates",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
