"""S2 marker-5 path-3 slide (FoT).

Grammar (same_canvas_rewrite):
  Background 7, path color 3, marker color 5. Each marker that orthogonally
  touches a path cell walks the path component (path cells only), finds the
  farthest degree-1 endpoint, clears the path + old marker to background,
  keeps that endpoint as path color, and places the marker on the cell just
  before the endpoint. Isolated markers (no path neighbor) stay put.

Canonical close: AGI-2 test task 182e5d0f.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]


def make_marker5_path3_slide(
    bg: int = 7, path: int = 3, marker: int = 5
) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        marks = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if inp[r][c] == marker
        ]
        if not marks:
            return None
        if not any(inp[r][c] == path for r in range(h) for c in range(w)):
            return None
        out = [list(row) for row in inp]
        moved = False
        for mr, mc in marks:
            nbs = [
                (mr + dr, mc + dc)
                for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0))
                if 0 <= mr + dr < h
                and 0 <= mc + dc < w
                and inp[mr + dr][mc + dc] == path
            ]
            if not nbs:
                continue
            start = nbs[0]
            q = deque([start])
            seen = {start}
            parent: Dict[Cell, Optional[Cell]] = {start: (mr, mc)}
            while q:
                x, y = q.popleft()
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and (nx, ny) not in seen
                        and inp[nx][ny] == path
                    ):
                        seen.add((nx, ny))
                        parent[(nx, ny)] = (x, y)
                        q.append((nx, ny))

            def deg(p: Cell) -> int:
                x, y = p
                d = 0
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    n = (x + dx, y + dy)
                    if n in seen or n == (mr, mc):
                        d += 1
                return d

            ends = [p for p in seen if deg(p) == 1]

            def depth(p: Cell) -> int:
                n = 0
                cur: Optional[Cell] = p
                while cur != (mr, mc) and cur in parent:
                    cur = parent[cur]
                    n += 1
                    if n > 1000:
                        break
                return n

            if not ends:
                continue
            end = max(ends, key=depth)
            out[mr][mc] = bg
            for x, y in seen:
                out[x][y] = bg
            place = parent[end]
            if place == (mr, mc):
                out[end[0]][end[1]] = marker
            else:
                assert place is not None
                out[end[0]][end[1]] = path
                out[place[0]][place[1]] = marker
            moved = True
        if not moved:
            return None
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("marker5_path3_slide", make_marker5_path3_slide())]


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
            "engine": "s2_marker5_path3_slide",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, _ = exact[0]
    passed = len(train)
    return {
        "engine": "s2_marker5_path3_slide",
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
