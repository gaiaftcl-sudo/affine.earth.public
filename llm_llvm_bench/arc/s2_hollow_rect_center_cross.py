"""S2 hollow-rect center cross (FoT).

Grammar (same_canvas_rewrite):
  Find each 4-connected hollow rectangle frame of color 1 on background 8.
  Through the center row and center column of each frame's bbox, paint
  background cells with 6 (frame 1s stay).

Canonical close: AGI-2 test task 41e4d17e.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Rect = Tuple[int, int, int, int]


def _hollow_rects(inp: Grid, frame: int = 1) -> List[Rect]:
    h, w = len(inp), len(inp[0])
    seen = set()
    rects: List[Rect] = []
    for r in range(h):
        for c in range(w):
            if inp[r][c] != frame or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            comp: List[Tuple[int, int]] = []
            while q:
                x, y = q.popleft()
                comp.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and inp[nx][ny] == frame
                        and (nx, ny) not in seen
                    ):
                        seen.add((nx, ny))
                        q.append((nx, ny))
            rs = [rr for rr, _ in comp]
            cs = [cc for _, cc in comp]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            if r1 - r0 < 2 or c1 - c0 < 2:
                continue
            expect = set()
            for cc in range(c0, c1 + 1):
                expect.add((r0, cc))
                expect.add((r1, cc))
            for rr in range(r0, r1 + 1):
                expect.add((rr, c0))
                expect.add((rr, c1))
            if set(comp) == expect:
                rects.append((r0, r1, c0, c1))
    return rects


def make_hollow_rect_center_cross(
    frame: int = 1, bg: int = 8, line: int = 6
) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        rects = _hollow_rects(inp, frame)
        if not rects:
            return None
        h, w = len(inp), len(inp[0])
        out = [row[:] for row in inp]
        for r0, r1, c0, c1 in rects:
            mr = (r0 + r1) // 2
            mc = (c0 + c1) // 2
            for c in range(w):
                if out[mr][c] == bg:
                    out[mr][c] = line
            for r in range(h):
                if out[r][mc] == bg:
                    out[r][mc] = line
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("hollow_rect_center_cross", make_hollow_rect_center_cross())]


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
            "engine": "s2_hollow_rect_center_cross",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_hollow_rect_center_cross",
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
