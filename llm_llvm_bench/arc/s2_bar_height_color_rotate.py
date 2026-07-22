"""S2 vertical-bar height/color rotate (FoT).

Grammar (same_canvas): extract bottom-aligned monochrome vertical bars on
background; keep bar columns; replace heights with left-rotated height list
and colors with right-rotated color list (same bar order left→right).

Canonical close: AGI-2 test task 2601afb7.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _extract_bars(inp: Grid, bg: int) -> List[Tuple[int, int, int]]:
    h, w = len(inp), len(inp[0])
    bars: List[Tuple[int, int, int]] = []
    for c in range(w):
        color = None
        height = 0
        for r in range(h - 1, -1, -1):
            v = inp[r][c]
            if v == bg:
                if height:
                    break
                continue
            if color is None:
                color = v
            if v != color:
                # not a clean bar
                color = None
                height = 0
                break
            height += 1
        # ensure no non-bg above the bar
        if color is not None and height > 0:
            top = h - height
            if all(inp[r][c] == bg for r in range(top)):
                bars.append((c, color, height))
            else:
                # allow only exact bottom bar with bg above
                if all(inp[r][c] == bg for r in range(0, h - height)):
                    bars.append((c, color, height))
    return bars


def rotate_bars(inp: Grid, bg: int) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    bars = _extract_bars(inp, bg)
    if len(bars) < 2:
        return None
    colors = [b[1] for b in bars]
    heights = [b[2] for b in bars]
    colors_out = colors[-1:] + colors[:-1]  # right rotate
    heights_out = heights[1:] + heights[:1]  # left rotate
    out = [[bg] * w for _ in range(h)]
    for (c, _, _), color, height in zip(bars, colors_out, heights_out):
        if height > h:
            return None
        for i in range(height):
            out[h - 1 - i][c] = color
    return out


def _learn_bg(train: Sequence[Dict[str, Any]]) -> Optional[int]:
    for bg in range(0, 10):
        if all(rotate_bars(ex["input"], bg) == ex["output"] for ex in train):
            return bg
    return None


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    bg = _learn_bg(train)
    if bg is None:
        return []

    def _xf(grid: Grid) -> Optional[Grid]:
        return rotate_bars(grid, bg)

    return [(f"bar_rot_bg{bg}", _xf)]


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
            "engine": "s2_bar_height_color_rotate",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_bar_height_color_rotate",
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
    "rotate_bars",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
