"""S2 T-marker axis erase-4 (FoT).

Grammar (same_canvas_rewrite):
  Three color-5 cells form a straight bar; one color-9 attaches on a side,
  making a T. Shoot away from the 9 through the bar. Erase (→7) every
  4-connected component of color 4 that lies entirely on the shoot side of
  the bar and intersects the T stem axis (9's column if the bar is horizontal,
  9's row if vertical).

Canonical close: AGI-2 test task 2f767503.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]


def _comps(inp: Grid, color: int = 4) -> List[List[Cell]]:
    h, w = len(inp), len(inp[0])
    seen = set()
    out: List[List[Cell]] = []
    for r in range(h):
        for c in range(w):
            if inp[r][c] != color or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells: List[Cell] = []
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and inp[nx][ny] == color
                        and (nx, ny) not in seen
                    ):
                        seen.add((nx, ny))
                        q.append((nx, ny))
            out.append(cells)
    return out


def make_t_marker_axis_erase4(
    bar: int = 5, stem: int = 9, erase: int = 4, bg: int = 7
) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        fives = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == bar]
        nines = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == stem]
        if len(fives) != 3 or len(nines) != 1:
            return None
        nine = nines[0]
        r0 = min(r for r, _ in fives)
        r1 = max(r for r, _ in fives)
        c0 = min(c for _, c in fives)
        c1 = max(c for _, c in fives)
        horizontal = r0 == r1
        vertical = c0 == c1
        if not (horizontal or vertical):
            return None
        if horizontal:
            if nine[0] > r1:
                on_shoot = lambda comp: max(r for r, _ in comp) < r0
            elif nine[0] < r0:
                on_shoot = lambda comp: min(r for r, _ in comp) > r1
            else:
                return None
            axis_hit = lambda comp: any(c == nine[1] for _, c in comp)
        else:
            if nine[1] > c1:
                on_shoot = lambda comp: max(c for _, c in comp) < c0
            elif nine[1] < c0:
                on_shoot = lambda comp: min(c for _, c in comp) > c1
            else:
                return None
            axis_hit = lambda comp: any(r == nine[0] for r, _ in comp)
        out = [row[:] for row in inp]
        erased = False
        for comp in _comps(inp, erase):
            if on_shoot(comp) and axis_hit(comp):
                for r, c in comp:
                    out[r][c] = bg
                erased = True
        if not erased:
            return None
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("t_marker_axis_erase4", make_t_marker_axis_erase4())]


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
            "engine": "s2_t_marker_axis_erase4",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_t_marker_axis_erase4",
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
