"""S2 odd-column max-8 pack-to-9 (FoT).

Grammar (same_canvas_rewrite):
  Even columns stay. Locate adjacent separator rows (2-row then 5-row).
  Global n8 = max count of color-8 over odd columns. Per odd column: pack from
  the top as [7]*start + [8]*n8 + [1]*n1 + [9]*tail where the 8-block ends on
  the 2-row and n1 is that column's input count of color-1. Licensed only on
  perfect train replay.

Canonical close: AGI-2 test task 41ace6b5.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_oddcol_max8_pack9() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        row2 = next((r for r in range(h) if inp[r].count(2) >= w // 2), None)
        row5 = next((r for r in range(h) if inp[r].count(5) >= w // 2), None)
        if row2 is None or row5 is None or row5 != row2 + 1:
            return None
        odd = list(range(1, w, 2))
        if not odd:
            return None
        n8 = max(sum(1 for r in range(h) if inp[r][c] == 8) for c in odd)
        out = [row[:] for row in inp]
        for c in odd:
            n1 = sum(1 for r in range(h) if inp[r][c] == 1)
            start = row2 - n8 + 1
            if start < 0:
                return None
            tail = h - start - n8 - n1
            if tail < 0:
                return None
            seq = [7] * start + [8] * n8 + [1] * n1 + [9] * tail
            for r in range(h):
                out[r][c] = seq[r]
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("oddcol_max8_pack9", make_oddcol_max8_pack9())]


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
            "engine": "s2_oddcol_max8_pack9",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_oddcol_max8_pack9",
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
