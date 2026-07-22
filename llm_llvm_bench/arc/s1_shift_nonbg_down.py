"""S1 shift all non-background cells down by one row (FoT).

Grammar (same_canvas): learn background; move every non-bg cell to (r+1, c);
cells that would leave the canvas are dropped; vacated cells become bg.

Canonical close: AGI-2 test task 25ff71a9.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def shift_nonbg_down(inp: Grid, bg: int) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    out: Grid = [[bg] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            v = inp[r][c]
            if v == bg:
                continue
            r2 = r + 1
            if r2 < h:
                out[r2][c] = v
    return out


def _learn_bg(train: Sequence[Dict[str, Any]]) -> Optional[int]:
    for bg in range(0, 10):
        if all(shift_nonbg_down(ex["input"], bg) == ex["output"] for ex in train):
            return bg
    return None


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    bg = _learn_bg(train)
    if bg is None:
        return []

    def _xf(grid: Grid) -> Optional[Grid]:
        return shift_nonbg_down(grid, bg)

    return [(f"shift_down_bg{bg}", _xf)]


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
            "engine": "s1_shift_nonbg_down",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_shift_nonbg_down",
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
    "shift_nonbg_down",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
