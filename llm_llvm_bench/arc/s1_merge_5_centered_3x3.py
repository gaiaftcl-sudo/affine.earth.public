"""S1 merge 5-centered 3x3 (FoT).

Grammar (zoom_in_crop):
  For every cell of color 5, take the 3x3 window centered on that cell (OOB as 0).
  Merge all windows by painting non-zero cells into a blank 3x3 (later non-zeros
  overwrite). The output is that merged 3x3 (center remains 5).

Canonical close: AGI-2 test task 137eaa0f.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_merge_5_centered_3x3() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        fives = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == 5]
        if not fives:
            return None
        out = [[0] * 3 for _ in range(3)]
        for r, c in fives:
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    rr, cc = r + dr, c + dc
                    v = 0
                    if 0 <= rr < h and 0 <= cc < w:
                        v = inp[rr][cc]
                    if v != 0:
                        out[dr + 1][dc + 1] = v
        if out[1][1] != 5:
            return None
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("merge_5_centered_3x3", make_merge_5_centered_3x3())]


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
            "engine": "s1_merge_5_centered_3x3",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_merge_5_centered_3x3",
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
