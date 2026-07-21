"""S2 diamond-hole stamp (FoT).

Grammar (same_canvas): for every non-empty cell C whose fixed diamond
offsets are all empty, clear C and stamp C's color onto that diamond.

Diamond offsets (relative to center):
  (1,2),(1,3),(2,1),(2,2),(2,3),(2,4),(3,1),(3,2),(3,3),(3,4),(4,2),(4,3)

Canonical close: AGI-2 test task 17b866bd (2 tests).
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

DIAMOND: Tuple[Tuple[int, int], ...] = (
    (1, 2),
    (1, 3),
    (2, 1),
    (2, 2),
    (2, 3),
    (2, 4),
    (3, 1),
    (3, 2),
    (3, 3),
    (3, 4),
    (4, 2),
    (4, 3),
)


def diamond_hole_stamp(inp: Grid, empty: int = 0) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    centers: List[Tuple[int, int, int]] = []
    for r in range(h):
        for c in range(w):
            col = inp[r][c]
            if col == empty:
                continue
            ok = True
            for dr, dc in DIAMOND:
                rr, cc = r + dr, c + dc
                if not (0 <= rr < h and 0 <= cc < w) or inp[rr][cc] != empty:
                    ok = False
                    break
            if ok:
                centers.append((r, c, col))
    if not centers:
        return None
    out = [list(row) for row in inp]
    for r, c, col in centers:
        out[r][c] = empty
        for dr, dc in DIAMOND:
            out[r + dr][c + dc] = col
    return out


def _learn_empty(train: Sequence[Dict[str, Any]]) -> Optional[int]:
    for empty in range(0, 10):
        if all(diamond_hole_stamp(ex["input"], empty) == ex["output"] for ex in train):
            return empty
    return None


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    empty = _learn_empty(train)
    if empty is None:
        return []

    def _xf(grid: Grid) -> Optional[Grid]:
        return diamond_hole_stamp(grid, empty)

    return [(f"diamond_hole_empty{empty}", _xf)]


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
            "engine": "s2_diamond_hole_stamp",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_diamond_hole_stamp",
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
    "DIAMOND",
    "applies",
    "diamond_hole_stamp",
    "exact_candidates",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
