"""S1 count 2×2 blocks → diagonal ones (FoT).

Grammar (zoom_in_crop): count solid 2×2 blocks of a learned color; emit an
N×N grid with that many `paint` cells on the main diagonal (rest 0).

Canonical close: AGI-2 test task 3b4c2228 (block=3, paint=1, N=3, 2 tests).
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def count_2x2(inp: Grid, block: int) -> int:
    h, w = len(inp), len(inp[0])
    n = 0
    for r in range(h - 1):
        for c in range(w - 1):
            if all(inp[r + dr][c + dc] == block for dr in (0, 1) for dc in (0, 1)):
                n += 1
    return n


def diag_from_count(inp: Grid, block: int, paint: int, size: int) -> Grid:
    n = count_2x2(inp, block)
    out = [[0] * size for _ in range(size)]
    for i in range(min(n, size)):
        out[i][i] = paint
    return out


def _learn(train: Sequence[Dict[str, Any]]) -> Optional[Tuple[int, int, int]]:
    for block in range(1, 10):
        for paint in range(1, 10):
            for size in (2, 3, 4, 5):
                if all(
                    diag_from_count(ex["input"], block, paint, size) == ex["output"]
                    for ex in train
                ):
                    return block, paint, size
    return None


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    params = _learn(train)
    if params is None:
        return []
    block, paint, size = params

    def _xf(grid: Grid) -> Optional[Grid]:
        if not grid or not grid[0]:
            return None
        return diag_from_count(grid, block, paint, size)

    return [(f"count2x2_{block}_diag{size}_paint{paint}", _xf)]


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
            "engine": "s1_count_2x2_diag_ones",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_count_2x2_diag_ones",
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
    "count_2x2",
    "diag_from_count",
    "exact_candidates",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
