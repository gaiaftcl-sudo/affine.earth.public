"""S2 border-color dock with edge-column extend (FoT).

Grammar (same_canvas_rewrite):
  Background = 7. Top border color = row-0 solid color; bottom border color =
  last-row solid color. Keep both border rows. 8-connected components of the
  top color (excluding the top border row) translate upward until blocked by
  non-background. 8-connected components of the bottom color (excluding the
  bottom border row) translate downward until blocked — except when a component
  lies entirely in a single left/right edge column (x=0 or x=W-1): then keep
  its cells and extend that column downward to the bottom interior. Licensed
  only on perfect train replay.

Canonical close: AGI-2 test task 17829a00.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_BG = 7
_DIRS8 = (
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1),
    (-1, -1),
    (-1, 1),
    (1, -1),
    (1, 1),
)


def _comps(inp: Grid, color: int, skip_rows: set) -> List[List[Tuple[int, int]]]:
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    out: List[List[Tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if r in skip_rows or seen[r][c] or inp[r][c] != color:
                continue
            cells: List[Tuple[int, int]] = []
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                y, x = q.popleft()
                cells.append((y, x))
                for dy, dx in _DIRS8:
                    ny, nx = y + dy, x + dx
                    if (
                        0 <= ny < h
                        and 0 <= nx < w
                        and ny not in skip_rows
                        and not seen[ny][nx]
                        and inp[ny][nx] == color
                    ):
                        seen[ny][nx] = True
                        q.append((ny, nx))
            out.append(cells)
    return out


def _border_color_dock_edge_extend(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    if h < 3:
        return None
    top, bot = inp[0][0], inp[-1][0]
    if any(v != top for v in inp[0]) or any(v != bot for v in inp[-1]):
        return None
    out = [[_BG] * w for _ in range(h)]
    out[0] = inp[0][:]
    out[-1] = inp[-1][:]

    def can_place(cells: List[Tuple[int, int]], dy: int) -> bool:
        for y, x in cells:
            ny = y + dy
            if ny <= 0 or ny >= h - 1:
                return False
            if out[ny][x] != _BG:
                return False
        return True

    def place(cells: List[Tuple[int, int]], dy: int, color: int) -> None:
        for y, x in cells:
            out[y + dy][x] = color

    top_comps = sorted(
        _comps(inp, top, {0}),
        key=lambda cs: (min(y for y, _ in cs), min(x for _, x in cs)),
    )
    for cells in top_comps:
        dy = 0
        while can_place(cells, dy - 1):
            dy -= 1
        place(cells, dy, top)

    bot_comps = sorted(
        _comps(inp, bot, {h - 1}),
        key=lambda cs: (-max(y for y, _ in cs), min(x for _, x in cs)),
    )
    for cells in bot_comps:
        xs = {x for _, x in cells}
        if xs == {0} or xs == {w - 1}:
            for y, x in cells:
                out[y][x] = bot
            c = next(iter(xs))
            max_r = max(y for y, _ in cells)
            for r in range(max_r, h - 1):
                out[r][c] = bot
        else:
            dy = 0
            while can_place(cells, dy + 1):
                dy += 1
            place(cells, dy, bot)
    return out


def make_border_color_dock_edge_extend() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _border_color_dock_edge_extend(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("border_color_dock_edge_extend", make_border_color_dock_edge_extend())]


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
            "engine": "s2_border_color_dock_edge_extend",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_border_color_dock_edge_extend",
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
