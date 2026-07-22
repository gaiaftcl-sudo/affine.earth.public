"""S2 seven-divider pack or rotate (FoT).

Grammar (same_canvas_rewrite):
  Per row:
  - If no 7: rotate left by 1.
  - If 7 present: subject = majority non-0/non-7 color.
    * Subject on both sides of the 7-block: place min(left,right) cells
      centered at the first 7.
    * Subject only on the right: left-pack length = start index of the
      right subject block.
    * Subject only on the left: right-pack length = n - (block_end + 1).

Canonical close: AGI-2 test task 2de01db2.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _solve_row(row: List[int]) -> Optional[List[int]]:
    n = len(row)
    if 7 not in row:
        return row[1:] + row[:1]
    others = [v for v in row if v not in (0, 7)]
    if not others:
        return [0] * n
    subj = Counter(others).most_common(1)[0][0]
    sevens = [i for i, v in enumerate(row) if v == 7]
    s0, s1 = sevens[0], sevens[-1]
    left_n = sum(1 for v in row[:s0] if v == subj)
    right_n = sum(1 for v in row[s1 + 1 :] if v == subj)
    out = [0] * n
    if left_n > 0 and right_n > 0:
        k = min(left_n, right_n)
        start = s0 - k // 2
        for i in range(k):
            if 0 <= start + i < n:
                out[start + i] = subj
        return out
    if right_n > left_n:
        right_cells = [i for i, v in enumerate(row) if v == subj and i > s1]
        if not right_cells:
            return None
        k = min(right_cells)
        for i in range(k):
            out[i] = subj
        return out
    left_cells = [i for i, v in enumerate(row) if v == subj and i < s0]
    if not left_cells:
        return out
    block_end = max(left_cells)
    k = n - (block_end + 1)
    for i in range(k):
        out[n - k + i] = subj
    return out


def seven_divider_pack_or_rotate(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    out: Grid = []
    for row in inp:
        solved = _solve_row(row)
        if solved is None or len(solved) != len(row):
            return None
        out.append(solved)
    return out


def make_seven_divider_pack_or_rotate() -> Transform:
    return seven_divider_pack_or_rotate


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("seven_divider_pack_or_rotate", make_seven_divider_pack_or_rotate())]


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
            "engine": "s2_seven_divider_pack_or_rotate",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_seven_divider_pack_or_rotate",
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
