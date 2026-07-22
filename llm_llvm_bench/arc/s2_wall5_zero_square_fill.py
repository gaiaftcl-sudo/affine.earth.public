"""S2 wall-5 zero square fill (FoT).

Grammar (same_canvas_rewrite):
  Input is a binary wall mask (color 5) on zeros. For each k in {2,3}, every
  k×k all-zero block that has at least one wall cell on each of its four sides
  (grid border counts as a satisfied side) is painted with fill color 1.
  Licensed only on perfect train replay.

Canonical close: AGI-2 test task 31adaf00.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_WALL = 5
_FILL = 1
_SIZES = (2, 3)


def _side_has_wall(g: Grid, coords: List[Tuple[int, int]], oob: bool, wall: int) -> bool:
    if oob:
        return True
    return any(g[r][c] == wall for r, c in coords)


def _fill_walled_zero_squares(inp: Grid, wall: int = _WALL, fill: int = _FILL) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    out = [row[:] for row in inp]
    for k in _SIZES:
        for r in range(h - k + 1):
            for c in range(w - k + 1):
                if not all(inp[rr][cc] == 0 for rr in range(r, r + k) for cc in range(c, c + k)):
                    continue
                top_oob = r - 1 < 0
                bot_oob = r + k >= h
                left_oob = c - 1 < 0
                right_oob = c + k >= w
                top = [(r - 1, cc) for cc in range(c, c + k)] if not top_oob else []
                bot = [(r + k, cc) for cc in range(c, c + k)] if not bot_oob else []
                left = [(rr, c - 1) for rr in range(r, r + k)] if not left_oob else []
                right = [(rr, c + k) for rr in range(r, r + k)] if not right_oob else []
                if not (
                    _side_has_wall(inp, top, top_oob, wall)
                    and _side_has_wall(inp, bot, bot_oob, wall)
                    and _side_has_wall(inp, left, left_oob, wall)
                    and _side_has_wall(inp, right, right_oob, wall)
                ):
                    continue
                for rr in range(r, r + k):
                    for cc in range(c, c + k):
                        out[rr][cc] = fill
    return out


def make_wall5_zero_square_fill() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _fill_walled_zero_squares(inp, wall=_WALL, fill=_FILL)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("wall5_zero_square_fill", make_wall5_zero_square_fill())]


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
            "engine": "s2_wall5_zero_square_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_wall5_zero_square_fill",
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
