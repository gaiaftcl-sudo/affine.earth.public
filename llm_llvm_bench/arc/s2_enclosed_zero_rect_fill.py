"""S2 enclosed zero-rect fill (FoT).

Grammar (same_canvas_rewrite):
  Find the largest axis-aligned all-zero rectangle that is enclosed (nonzero
  or border on all four sides). Fill it with the learned fill color.

Canonical close: AGI-2 test task 3eda0437.
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
        for r, row in enumerate(gi):
            for c, v in enumerate(row):
                if v == 0 and go[r][c] != 0:
                    votes[go[r][c]] += 1
    if not votes:
        return None
    return votes.most_common(1)[0][0]


def make_fill(fill: int) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        best: Optional[Tuple[int, int, int, int, int]] = None
        for r0 in range(h):
            for r1 in range(r0, h):
                for c0 in range(w):
                    for c1 in range(c0, w):
                        hh, ww = r1 - r0 + 1, c1 - c0 + 1
                        if hh < 2 or ww < 2:
                            continue
                        if not all(
                            inp[r][c] == 0
                            for r in range(r0, r1 + 1)
                            for c in range(c0, c1 + 1)
                        ):
                            continue
                        left_ok = c0 == 0 or any(
                            inp[r][c0 - 1] != 0 for r in range(r0, r1 + 1)
                        )
                        right_ok = c1 == w - 1 or any(
                            inp[r][c1 + 1] != 0 for r in range(r0, r1 + 1)
                        )
                        top_ok = r0 == 0 or any(
                            inp[r0 - 1][c] != 0 for c in range(c0, c1 + 1)
                        )
                        bot_ok = r1 == h - 1 or any(
                            inp[r1 + 1][c] != 0 for c in range(c0, c1 + 1)
                        )
                        if not (left_ok and right_ok and top_ok and bot_ok):
                            continue
                        area = hh * ww
                        if best is None or area > best[0]:
                            best = (area, r0, r1, c0, c1)
        if best is None:
            return None
        _, r0, r1, c0, c1 = best
        out = [row[:] for row in inp]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = fill
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    fill = _learn_fill(train)
    if fill is None:
        return []
    return [("enclosed_zero_rect_fill", make_fill(fill))]


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
            "engine": "s2_enclosed_zero_rect_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_enclosed_zero_rect_fill",
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
