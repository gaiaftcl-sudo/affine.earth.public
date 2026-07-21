"""S2 marker-freq column project (FoT).

Grammar (same_canvas_rewrite):
  Top-row marker count n (contiguous 8s) selects digit-row columns whose value
  appears exactly n times; project those digits upward n rows above a solid
  separator bar (color 5).

Canonical close: AGI-2 test task 2685904e.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _project(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    n = 0
    for c in range(w):
        if inp[0][c] == 8:
            n += 1
        else:
            break
    if n == 0:
        return None
    sep = [r for r in range(h) if sum(1 for x in inp[r] if x == 5) == w]
    if not sep:
        return None
    sr = sep[0]
    dr = None
    for r in range(sr + 1, h):
        if any(inp[r][c] not in (0, 5) for c in range(w)):
            dr = r
            break
    if dr is None:
        return None
    digits = inp[dr]
    freq = Counter(digits)
    out = [list(row) for row in inp]
    for c in range(w):
        v = digits[c]
        if v != 0 and freq[v] == n:
            for k in range(1, n + 1):
                rr = sr - k
                if rr < 0:
                    return None
                if out[rr][c] == 0:
                    out[rr][c] = v
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("marker_freq_column_project", _project)]


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
            "engine": "s2_marker_freq_column_project",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_marker_freq_column_project",
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
