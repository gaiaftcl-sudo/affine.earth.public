"""S2 singleton skip-ray + border (FoT).

Grammar (same_canvas_rewrite):
  Background = majority color. Each non-bg color that appears exactly once
  shoots along its longest clear-bg orthogonal ray, painting every other
  cell (odd steps). On reaching a canvas edge, fill that entire border
  edge with the singleton color (bg cells only). If one singleton shoots
  up and another shoots horizontally, zero the top corner in the
  horizontal shoot direction.

Canonical close: AGI-2 test task 13f06aa5.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_singleton_skipray_border() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        bg = Counter(v for row in inp for v in row).most_common(1)[0][0]
        ctr = Counter(v for row in inp for v in row if v != bg)
        singles = [col for col, n in ctr.items() if n == 1]
        if not singles:
            return None
        out = [row[:] for row in inp]
        shots: List[Tuple[int, int, int, int, int]] = []
        for col in singles:
            r, c = next(
                (rr, cc) for rr in range(h) for cc in range(w) if inp[rr][cc] == col
            )
            dirs = []
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                dist = 0
                while 0 <= rr < h and 0 <= cc < w and inp[rr][cc] == bg:
                    dist += 1
                    rr += dr
                    cc += dc
                dirs.append((dist, dr, dc))
            dirs.sort(reverse=True)
            dist, dr, dc = dirs[0]
            if dist == 0:
                continue
            shots.append((col, r, c, dr, dc))
            step = 0
            rr, cc = r + dr, c + dc
            while 0 <= rr < h and 0 <= cc < w and inp[rr][cc] == bg:
                if step % 2 == 1:
                    out[rr][cc] = col
                step += 1
                rr += dr
                cc += dc
            if dr == -1:
                for x in range(w):
                    if inp[0][x] == bg:
                        out[0][x] = col
            elif dr == 1:
                for x in range(w):
                    if inp[h - 1][x] == bg:
                        out[h - 1][x] = col
            elif dc == -1:
                for y in range(h):
                    if inp[y][0] == bg:
                        out[y][0] = col
            elif dc == 1:
                for y in range(h):
                    if inp[y][w - 1] == bg:
                        out[y][w - 1] = col
        up = [s for s in shots if s[3] == -1]
        hz = [s for s in shots if s[4] != 0]
        if up and hz:
            _col, _r, _c, _dr, dc = hz[0]
            if dc == 1:
                out[0][w - 1] = 0
            elif dc == -1:
                out[0][0] = 0
        if out == [row[:] for row in inp]:
            return None
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("singleton_skipray_border", make_singleton_skipray_border())]


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
            "engine": "s2_singleton_skipray_border",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_singleton_skipray_border",
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
