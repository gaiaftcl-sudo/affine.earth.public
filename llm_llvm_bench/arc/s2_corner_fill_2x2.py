"""S2 corner-fill 2x2 (FoT).

Grammar (same_canvas_rewrite):
  For every 2×2 window that contains exactly three cells of a learned
  wall color and one zero, write a learned fill color into the zero.

Canonical close: AGI-2 test task 3aa6fb7a.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _learn(train: Sequence[Dict[str, Any]]) -> Optional[Tuple[int, int]]:
    wall_votes = Counter()
    fill_votes = Counter()
    for example in train:
        gi, go = example["input"], example["output"]
        if len(gi) != len(go) or (gi and len(gi[0]) != len(go[0])):
            return None
        h, w = len(gi), len(gi[0])
        for r in range(h - 1):
            for c in range(w - 1):
                cells = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
                vals = [gi[x][y] for x, y in cells]
                outs = [go[x][y] for x, y in cells]
                if vals.count(0) != 1:
                    continue
                nonzero = [v for v in vals if v != 0]
                if len(set(nonzero)) != 1 or len(nonzero) != 3:
                    continue
                wall = nonzero[0]
                # exactly one cell changed 0 -> fill
                changed = [(outs[i], cells[i]) for i, v in enumerate(vals) if v == 0]
                if len(changed) != 1:
                    return None
                fill, _ = changed[0]
                if fill == 0:
                    return None
                wall_votes[wall] += 1
                fill_votes[fill] += 1
    if not wall_votes or not fill_votes:
        return None
    return wall_votes.most_common(1)[0][0], fill_votes.most_common(1)[0][0]


def make_fill(wall: int, fill: int) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        out = [list(row) for row in inp]
        for r in range(h - 1):
            for c in range(w - 1):
                cells = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
                vals = [inp[x][y] for x, y in cells]
                if vals.count(wall) == 3 and vals.count(0) == 1:
                    for x, y in cells:
                        if inp[x][y] == 0:
                            out[x][y] = fill
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    learned = _learn(train)
    if learned is None:
        return []
    wall, fill = learned
    return [("corner_fill_2x2", make_fill(wall, fill))]


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
            "engine": "s2_corner_fill_2x2",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_corner_fill_2x2",
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
