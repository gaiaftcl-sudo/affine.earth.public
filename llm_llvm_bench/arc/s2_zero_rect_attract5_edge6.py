"""S2 zero-rect attract-5 edge-6 (FoT).

Grammar (same_canvas_rewrite):
  Background 7, zero blobs of color 0, attractor color 5. For each 0-component
  that shares a row with any 5, take the largest solid rectangle inside the
  blob, clear protrusion zeros to background, and paint the rectangle edge
  facing the nearby 5s as color 6 (left if attractors are left of center,
  else right).

Canonical close: AGI-2 test task 3d588dc9.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]


def make_zero_rect_attract5_edge6(
    bg: int = 7, zero: int = 0, paint: int = 6, attract: int = 5
) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        attractors = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if inp[r][c] == attract
        ]
        if not attractors:
            return None
        attract_rows = {r for r, _ in attractors}
        out = [list(row) for row in inp]
        seen = [[False] * w for _ in range(h)]
        painted = False
        for r in range(h):
            for c in range(w):
                if inp[r][c] != zero or seen[r][c]:
                    continue
                q = deque([(r, c)])
                seen[r][c] = True
                cells: List[Cell] = []
                while q:
                    x, y = q.popleft()
                    cells.append((x, y))
                    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                        nx, ny = x + dx, y + dy
                        if (
                            0 <= nx < h
                            and 0 <= ny < w
                            and not seen[nx][ny]
                            and inp[nx][ny] == zero
                        ):
                            seen[nx][ny] = True
                            q.append((nx, ny))
                rows = {x for x, _ in cells}
                if not (rows & attract_rows):
                    continue
                cellset = set(cells)
                rs = [x for x, _ in cells]
                cs = [y for _, y in cells]
                r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
                best = None
                best_a = 0
                for a in range(r0, r1 + 1):
                    for b in range(a, r1 + 1):
                        for left in range(c0, c1 + 1):
                            for right in range(left, c1 + 1):
                                if all(
                                    (rr, cc) in cellset
                                    for rr in range(a, b + 1)
                                    for cc in range(left, right + 1)
                                ):
                                    area = (b - a + 1) * (right - left + 1)
                                    if area > best_a:
                                        best_a = area
                                        best = (a, b, left, right)
                if not best or best_a < 4:
                    continue
                a, b, left, right = best
                rect = {
                    (rr, cc)
                    for rr in range(a, b + 1)
                    for cc in range(left, right + 1)
                }
                for x, y in cells:
                    if (x, y) not in rect:
                        out[x][y] = bg
                near_a = [
                    (ar, ac)
                    for ar, ac in attractors
                    if ar in rows
                    or any(abs(ar - x) + abs(ac - y) <= 5 for x, y in cells)
                ]
                use = near_a if near_a else attractors
                acx = sum(ac for _, ac in use) / len(use)
                edge = left if acx < (left + right) / 2 else right
                for rr in range(a, b + 1):
                    out[rr][edge] = paint
                painted = True
        if not painted:
            return None
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("zero_rect_attract5_edge6", make_zero_rect_attract5_edge6())]


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
            "engine": "s2_zero_rect_attract5_edge6",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, _ = exact[0]
    passed = len(train)
    return {
        "engine": "s2_zero_rect_attract5_edge6",
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
