"""S2 monochromatic-row recolor (FoT).

Grammar (same_canvas_rewrite):
  Any row whose cells are all the same nonzero color is rewritten to a
  learned fill color across the full row; every other row becomes zeros.

Canonical close: AGI-2 test task 25d8a9c8.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _learn_fill(train: Sequence[Dict[str, Any]]) -> Optional[int]:
    fills = Counter()
    for example in train:
        gi, go = example["input"], example["output"]
        if len(gi) != len(go) or (gi and len(gi[0]) != len(go[0])):
            return None
        for r in range(len(gi)):
            vals = set(gi[r])
            if len(vals) == 1 and 0 not in vals:
                out_vals = set(go[r])
                if len(out_vals) != 1:
                    return None
                fills[next(iter(out_vals))] += 1
    if not fills:
        return None
    return fills.most_common(1)[0][0]


def make_recolor(fill: int) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        out = [[0] * w for _ in range(h)]
        for r in range(h):
            vals = set(inp[r])
            if len(vals) == 1 and 0 not in vals:
                out[r] = [fill] * w
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    fill = _learn_fill(train)
    if fill is None:
        return []
    return [("mono_row_recolor", make_recolor(fill))]


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
            "engine": "s2_mono_row_recolor",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_mono_row_recolor",
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
