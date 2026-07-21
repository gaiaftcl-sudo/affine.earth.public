"""S2 drop markers into floor row (FoT).

Grammar (same_canvas_rewrite):
  Learned marker cells fall straight down within their column onto the
  lowest floor-colored cell in that column (replacing it). Marker source
  cells clear to zero. Other cells unchanged.

Canonical close: AGI-2 test task 3618c87e.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _learn(train: Sequence[Dict[str, Any]]) -> Optional[Tuple[int, int]]:
    marker_votes = Counter()
    floor_votes = Counter()
    for example in train:
        gi, go = example["input"], example["output"]
        if len(gi) != len(go) or (gi and len(gi[0]) != len(go[0])):
            return None
        h, w = len(gi), len(gi[0])
        # markers: colors present in input that disappear from their cells
        disappeared = []
        for r in range(h):
            for c in range(w):
                if gi[r][c] != 0 and go[r][c] == 0:
                    disappeared.append(gi[r][c])
        if not disappeared:
            return None
        marker = Counter(disappeared).most_common(1)[0][0]
        # floor: color replaced by marker in output
        floors = []
        for r in range(h):
            for c in range(w):
                if go[r][c] == marker and gi[r][c] != marker:
                    floors.append(gi[r][c])
        if not floors:
            return None
        floor = Counter(floors).most_common(1)[0][0]
        marker_votes[marker] += 1
        floor_votes[floor] += 1
    if not marker_votes or not floor_votes:
        return None
    return marker_votes.most_common(1)[0][0], floor_votes.most_common(1)[0][0]


def make_drop(marker: int, floor: int) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        out = [list(row) for row in inp]
        markers = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == marker]
        for r, c in markers:
            out[r][c] = 0
        for r, c in markers:
            target = None
            for rr in range(h - 1, r, -1):
                if out[rr][c] == floor:
                    target = rr
                    break
            if target is None:
                return None
            out[target][c] = marker
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    learned = _learn(train)
    if learned is None:
        return []
    marker, floor = learned
    return [("drop_into_floor_row", make_drop(marker, floor))]


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
            "engine": "s2_drop_into_floor_row",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_drop_into_floor_row",
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
