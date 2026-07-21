"""S2 top-pattern stamp on right marks (FoT).

Grammar (same_canvas_rewrite):
  Row 0 is a template of marker color M. Every other row that contains a
  lone M on the rightmost column receives a recolored copy of the row-0
  pattern (nonzero cells become a learned stamp color), keeping the
  right-edge M.

Canonical close: AGI-2 test task 2281f1f4.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _learn(train: Sequence[Dict[str, Any]]) -> Optional[Tuple[int, int]]:
    marker_votes = Counter()
    stamp_votes = Counter()
    for example in train:
        gi, go = example["input"], example["output"]
        if len(gi) != len(go) or (gi and len(gi[0]) != len(go[0])):
            return None
        top = [v for v in gi[0] if v != 0]
        if not top:
            return None
        if len(set(top)) != 1:
            return None
        marker = top[0]
        marker_votes[marker] += 1
        # stamp color from first changed row
        found = None
        for r in range(1, len(gi)):
            for c in range(len(gi[0])):
                if gi[r][c] == 0 and go[r][c] not in (0, marker):
                    found = go[r][c]
                    break
            if found is not None:
                break
        if found is None:
            return None
        stamp_votes[found] += 1
    if not marker_votes or not stamp_votes:
        return None
    return marker_votes.most_common(1)[0][0], stamp_votes.most_common(1)[0][0]


def make_stamp(marker: int, stamp: int) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        top = inp[0]
        if any(v not in (0, marker) for v in top) or marker not in top:
            return None
        out = [list(row) for row in inp]
        pattern_cols = [c for c in range(w) if top[c] == marker]
        for r in range(1, h):
            if inp[r][w - 1] != marker:
                continue
            if any(inp[r][c] != 0 for c in range(w - 1)):
                continue
            for c in pattern_cols:
                if c == w - 1:
                    continue
                out[r][c] = stamp
            out[r][w - 1] = marker
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    learned = _learn(train)
    if learned is None:
        return []
    marker, stamp = learned
    return [("top_pattern_stamp_on_right_marks", make_stamp(marker, stamp))]


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
            "engine": "s2_top_pattern_stamp_on_right_marks",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_top_pattern_stamp_on_right_marks",
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
