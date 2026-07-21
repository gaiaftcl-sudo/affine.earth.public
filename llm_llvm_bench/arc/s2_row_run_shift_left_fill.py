"""S2 row-run shift-left fill (FoT).

Grammar (same_canvas_rewrite):
  Each contiguous horizontal run of a non-zero color shifts left by one cell,
  clipping at the left edge (cells that would leave the canvas are dropped).
  Remaining cells fill with a learned fill color (constant across train).

Canonical close: AGI-2 test task 32e9702f.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _learn_fill(train: Sequence[Dict[str, Any]]) -> Optional[int]:
    votes: Counter = Counter()
    for example in train:
        gi, go = example["input"], example["output"]
        if len(gi) != len(go) or len(gi[0]) != len(go[0]):
            return None
        for r, row in enumerate(gi):
            for c, v in enumerate(row):
                if v == 0 and go[r][c] != 0:
                    votes[go[r][c]] += 1
    if not votes:
        return None
    return votes.most_common(1)[0][0]


def make_shift_fill(fill: int) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        out = [[fill] * w for _ in range(h)]
        for r in range(h):
            c = 0
            while c < w:
                if inp[r][c] == 0:
                    c += 1
                    continue
                col = inp[r][c]
                c0 = c
                while c < w and inp[r][c] == col:
                    c += 1
                for x in range(c0, c):
                    nx = x - 1
                    if nx >= 0:
                        out[r][nx] = col
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    fill = _learn_fill(train)
    if fill is None:
        return []
    return [("row_run_shift_left_fill", make_shift_fill(fill))]


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
            "engine": "s2_row_run_shift_left_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_row_run_shift_left_fill",
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
    "solve_task",
    "submission_fragment",
    "train_replay",
]
