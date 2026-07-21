"""S1 odd hole-count tile (FoT).

Grammar (zoom_in_crop):
  Extract same-color 4-connected components whose tight bbox matches the
  learned tile size and contains only that color + zeros (holes). Among those
  tiles, return the one whose hole count is unique (odd-one-out).

Canonical close: AGI-2 test task 358ba94e.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _learn_tile_shape(train: Sequence[Dict[str, Any]]) -> Optional[Tuple[int, int]]:
    shapes = {(len(ex["output"]), len(ex["output"][0])) for ex in train}
    if len(shapes) != 1:
        return None
    return next(iter(shapes))


def _tiles(grid: Grid, oh: int, ow: int) -> List[Tuple[int, Tuple[Tuple[int, ...], ...]]]:
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    out: List[Tuple[int, Tuple[Tuple[int, ...], ...]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or seen[r][c]:
                continue
            col0 = grid[r][c]
            cells: List[Tuple[int, int]] = []
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and not seen[nx][ny]
                        and grid[nx][ny] == col0
                    ):
                        seen[nx][ny] = True
                        q.append((nx, ny))
            rs = [x for x, _ in cells]
            cs = [y for _, y in cells]
            r0, r1 = min(rs), max(rs)
            c0, c1 = min(cs), max(cs)
            if r1 - r0 + 1 != oh or c1 - c0 + 1 != ow:
                continue
            if any(
                grid[r0 + i][c0 + j] not in (0, col0)
                for i in range(oh)
                for j in range(ow)
            ):
                continue
            pat = tuple(
                tuple(grid[r0 + i][c0 + j] for j in range(ow)) for i in range(oh)
            )
            holes = sum(1 for row in pat for v in row if v == 0)
            out.append((holes, pat))
    return out


def make_odd_hole(oh: int, ow: int) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        blocks = _tiles(inp, oh, ow)
        if not blocks:
            return None
        hcnt = Counter(h for h, _ in blocks)
        odd = [t for h, t in blocks if hcnt[h] == 1]
        if len(odd) == 1:
            return [list(row) for row in odd[0]]
        pc = Counter(t for _, t in blocks)
        uniq = [t for t, n in pc.items() if n == 1]
        if len(uniq) == 1:
            return [list(row) for row in uniq[0]]
        return None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    shape = _learn_tile_shape(train)
    if shape is None:
        return []
    oh, ow = shape
    return [("odd_hole_count_tile", make_odd_hole(oh, ow))]


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
            "engine": "s1_odd_hole_count_tile",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_odd_hole_count_tile",
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
    "solve_task",
    "submission_fragment",
    "train_replay",
]
