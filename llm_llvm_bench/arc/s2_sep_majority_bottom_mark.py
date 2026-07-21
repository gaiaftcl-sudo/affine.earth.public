"""S2 separator majority bottom mark (FoT).

Grammar (same_canvas_rewrite):
  Find the first solid separator row (all cells one nonzero color).
  Among nonzero non-separator colors above it, take the majority color
  and write it at the bottom-center cell of the canvas (clearing all
  rows below the separator first).

Canonical close: AGI-2 test task 27a77e38.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def sep_majority_bottom_mark(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    sep = None
    sepc = None
    for r in range(h):
        vals = set(inp[r])
        if len(vals) == 1 and 0 not in vals:
            sep = r
            sepc = next(iter(vals))
            break
    if sep is None or sepc is None:
        return None
    counts: Counter = Counter()
    for r in range(sep):
        for c in range(w):
            v = inp[r][c]
            if v not in (0, sepc):
                counts[v] += 1
    if not counts:
        return None
    color = counts.most_common(1)[0][0]
    out = [list(row) for row in inp]
    for r in range(sep + 1, h):
        out[r] = [0] * w
    out[h - 1][w // 2] = color
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("sep_majority_bottom_mark", sep_majority_bottom_mark)]


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
            "engine": "s2_sep_majority_bottom_mark",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_sep_majority_bottom_mark",
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
    "sep_majority_bottom_mark",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
