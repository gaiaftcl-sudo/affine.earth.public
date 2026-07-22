"""S2 clockwise gap spiral (FoT).

Grammar (same_canvas_rewrite):
  Ignore input content; canvas size N = len(input).
  Paint color 3 along a clockwise gap-spiral starting at (0,0):
  leg lengths [N-1, N-1, N-1] then pairs (N-3, N-3), (N-5, N-5), ... while > 0.

Canonical close: AGI-2 test task 28e73c20.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _leg_lengths(n: int) -> List[int]:
    if n <= 1:
        return []
    legs = [n - 1, n - 1, n - 1]
    k = n - 3
    while k > 0:
        legs.extend([k, k])
        k -= 2
    return legs


def clockwise_gap_spiral(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    n = len(inp)
    if any(len(row) != n for row in inp):
        return None
    out: Grid = [[0] * n for _ in range(n)]
    r = c = 0
    out[0][0] = 3
    dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    d = 0
    for length in _leg_lengths(n):
        dr, dc = dirs[d]
        for _ in range(length):
            r += dr
            c += dc
            if not (0 <= r < n and 0 <= c < n):
                return None
            out[r][c] = 3
        d = (d + 1) % 4
    return out


def make_clockwise_gap_spiral() -> Transform:
    return clockwise_gap_spiral


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("clockwise_gap_spiral", make_clockwise_gap_spiral())]


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
            "engine": "s2_clockwise_gap_spiral",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_clockwise_gap_spiral",
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
