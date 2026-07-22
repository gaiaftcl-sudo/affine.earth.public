"""S2 zero-seed cross preserve-2 (FoT).

Grammar (same_canvas_rewrite):
  Locate the bounding box of color-0 cells (the seed). Zero every cell in the
  full row-band and column-band cross of that box, except cells already color 2
  (those stay 2). Seed zeros remain zero.

Canonical close: AGI-2 test task 319f2597.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_zero_seed_cross_preserve2(preserve: int = 2) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        zeros = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == 0]
        if not zeros:
            return None
        rs = [r for r, _ in zeros]
        cs = [c for _, c in zeros]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        out = [row[:] for row in inp]
        for r in range(h):
            for c in range(c0, c1 + 1):
                if out[r][c] != preserve:
                    out[r][c] = 0
        for r in range(r0, r1 + 1):
            for c in range(w):
                if out[r][c] != preserve:
                    out[r][c] = 0
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("zero_seed_cross_preserve2", make_zero_seed_cross_preserve2())]


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
            "engine": "s2_zero_seed_cross_preserve2",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_zero_seed_cross_preserve2",
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
