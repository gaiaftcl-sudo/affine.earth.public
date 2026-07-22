"""S2 largest host-frame interior crop (FoT).

Grammar (zoom_in_crop):
  Take the largest 4-connected nonzero component; its color is the host.
  Among axis-aligned rectangles whose entire border is host color and whose
  interior contains at least one non-host cell, choose the maximum interior
  area. Return that interior (strip the 1-cell host frame). Licensed only on
  perfect train replay.

Canonical close: AGI-2 test task 1a6449f1.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _largest_host(inp: Grid) -> Optional[int]:
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    dirs = ((-1, 0), (1, 0), (0, -1), (0, 1))
    best_color: Optional[int] = None
    best_size = 0
    for r in range(h):
        for c in range(w):
            if seen[r][c] or inp[r][c] == 0:
                continue
            color = inp[r][c]
            size = 0
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                y, x = q.popleft()
                size += 1
                for dy, dx in dirs:
                    ny, nx = y + dy, x + dx
                    if (
                        0 <= ny < h
                        and 0 <= nx < w
                        and not seen[ny][nx]
                        and inp[ny][nx] == color
                    ):
                        seen[ny][nx] = True
                        q.append((ny, nx))
            if size > best_size:
                best_size = size
                best_color = color
    return best_color


def _is_host_frame(inp: Grid, r0: int, c0: int, r1: int, c1: int, host: int) -> bool:
    if r1 - r0 < 2 or c1 - c0 < 2:
        return False
    for c in range(c0, c1 + 1):
        if inp[r0][c] != host or inp[r1][c] != host:
            return False
    for r in range(r0, r1 + 1):
        if inp[r][c0] != host or inp[r][c1] != host:
            return False
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            if inp[r][c] != host:
                return True
    return False


def _largest_host_frame_interior(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    host = _largest_host(inp)
    if host is None:
        return None
    h, w = len(inp), len(inp[0])
    best: Optional[Tuple[int, Grid]] = None
    for r0 in range(h):
        for r1 in range(r0 + 2, h):
            for c0 in range(w):
                for c1 in range(c0 + 2, w):
                    if not _is_host_frame(inp, r0, c0, r1, c1, host):
                        continue
                    interior = [row[c0 + 1 : c1] for row in inp[r0 + 1 : r1]]
                    area = (r1 - r0 - 1) * (c1 - c0 - 1)
                    if best is None or area > best[0]:
                        best = (area, interior)
    return None if best is None else best[1]


def make_largest_host_frame_interior() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _largest_host_frame_interior(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("largest_host_frame_interior", make_largest_host_frame_interior())]


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
            "engine": "s2_largest_host_frame_interior",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_largest_host_frame_interior",
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
