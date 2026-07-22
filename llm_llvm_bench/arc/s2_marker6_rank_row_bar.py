"""S2 marker-6 rank row bar (FoT).

Grammar (same_canvas_rewrite):
  Background = 7. For each row containing a 6, let marks be the columns whose
  cell is not background. Paint a contiguous bar of 8s of length len(marks)
  whose position keeps the 6 at the same rank index among the marks
  (start = six_col - rank). All other cells become background.
  Licensed only on perfect train replay.

Canonical close: AGI-2 test task 2a28add5.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_BG = 7
_MARKER = 6
_FILL = 8


def _marker6_rank_row_bar(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    out = [[_BG] * w for _ in range(h)]
    for r in range(h):
        marks = [c for c in range(w) if inp[r][c] != _BG]
        sixes = [c for c in marks if inp[r][c] == _MARKER]
        if not sixes:
            continue
        for six in sixes:
            idx = marks.index(six)
            n = len(marks)
            start = six - idx
            for c in range(start, start + n):
                if 0 <= c < w:
                    out[r][c] = _FILL
    return out


def make_marker6_rank_row_bar() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _marker6_rank_row_bar(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("marker6_rank_row_bar", make_marker6_rank_row_bar())]


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
            "engine": "s2_marker6_rank_row_bar",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_marker6_rank_row_bar",
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
