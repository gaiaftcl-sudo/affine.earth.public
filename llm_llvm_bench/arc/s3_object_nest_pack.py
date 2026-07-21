"""Batch FoT engine for eval task 7491f3cf.

Grammar family owned here:
  object_nest_pack (canonical: eval task 7491f3cf)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 7491f3cf). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def object_nest_pack(grid: Grid) -> Optional[Grid]:
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
Puzzle 7491f3cf: Panel combination guided by dividing line.

The 7x25 grid has 4 panels of 5x5 separated by a border color.
Panel 1 defines a dividing line that splits the 5x5 area into two regions.
The smaller region is filled with Panel 2's pattern, the larger with Panel 3's.
On the dividing line itself, Panel 2 takes priority if non-background, else Panel 3.
Panel 4 (initially blank) gets the combined result.
"""
from collections import deque
import json
import sys


def _solve(grid: list[list[int]]) -> list[list[int]]:
    H, W = 5, 5
    border = grid[0][0]
    bg = grid[1][19]  # Panel 4 background

    # Extract panels (rows 1-5, different column offsets)
    p1 = [[grid[r + 1][c + 1] for c in range(W)] for r in range(H)]
    p2 = [[grid[r + 1][c + 7] for c in range(W)] for r in range(H)]
    p3 = [[grid[r + 1][c + 13] for c in range(W)] for r in range(H)]

    # Panel 1 mask: colored (non-bg) cells form the dividing line
    mask = [[p1[r][c] != bg for c in range(W)] for r in range(H)]

    # Flood-fill to find connected components of non-line cells
    comp = [[-1] * W for _ in range(H)]
    cid = 0
    sizes: dict[int, int] = {}
    for sr in range(H):
        for sc in range(W):
            if mask[sr][sc] or comp[sr][sc] != -1:
                continue
            q = deque([(sr, sc)])
            comp[sr][sc] = cid
            sz = 0
            while q:
                r, c = q.popleft()
                sz += 1
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < H and 0 <= nc < W and not mask[nr][nc] and comp[nr][nc] == -1:
                        comp[nr][nc] = cid
                        q.append((nr, nc))
            sizes[cid] = sz
            cid += 1

    # Smaller component gets Panel 2, larger gets Panel 3
    sorted_c = sorted(sizes.keys(), key=lambda k: sizes[k])
    p2_comp = sorted_c[0]
    p3_comp = sorted_c[1]

    output = [row[:] for row in grid]

    for r in range(H):
        for c in range(W):
            if not mask[r][c]:
                # Cell belongs to a region
                if comp[r][c] == p2_comp:
                    output[r + 1][c + 19] = p2[r][c]
                else:
                    output[r + 1][c + 19] = p3[r][c]
            else:
                # Dividing line cell: check which regions it borders
                b2 = any(
                    0 <= r + dr < H and 0 <= c + dc < W
                    and not mask[r + dr][c + dc]
                    and comp[r + dr][c + dc] == p2_comp
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                )
                b3 = any(
                    0 <= r + dr < H and 0 <= c + dc < W
                    and not mask[r + dr][c + dc]
                    and comp[r + dr][c + dc] == p3_comp
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                )
                if b2 and b3:
                    output[r + 1][c + 19] = p2[r][c] if p2[r][c] != bg else p3[r][c]
                elif b2:
                    output[r + 1][c + 19] = p2[r][c]
                elif b3:
                    output[r + 1][c + 19] = p3[r][c]
                else:
                    output[r + 1][c + 19] = bg

    return output



def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("object_nest_pack", object_nest_pack)]


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
            "engine": "s3_object_nest_pack",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_object_nest_pack",
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
    "object_nest_pack",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
