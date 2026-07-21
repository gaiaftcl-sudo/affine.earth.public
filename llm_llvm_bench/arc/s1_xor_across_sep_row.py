"""S1 XOR across separator row (FoT).

Grammar (zoom_in_crop): a solid nonzero separator row splits the canvas into
equal top/bottom halves; emit paint where exactly one half is nonzero (XOR).

Canonical close: AGI-2 test task 3428a4f5 (paint=3, 2 tests).
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def xor_across_sep_row(inp: Grid, paint: int, sep_color: Optional[int] = None) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    if sep_color is None:
        seps = [r for r in range(h) if len(set(inp[r])) == 1 and inp[r][0] != 0]
    else:
        seps = [r for r in range(h) if len(set(inp[r])) == 1 and inp[r][0] == sep_color]
    if len(seps) != 1:
        return None
    sr = seps[0]
    top, bot = inp[:sr], inp[sr + 1 :]
    if len(top) != len(bot) or not top:
        return None
    out: Grid = []
    for r in range(len(top)):
        row: List[int] = []
        for c in range(w):
            a = top[r][c] != 0
            b = bot[r][c] != 0
            row.append(paint if (a ^ b) else 0)
        out.append(row)
    return out


def _learn_params(train: Sequence[Dict[str, Any]]) -> Optional[Tuple[int, int]]:
    for paint in range(1, 10):
        for sep_color in range(1, 10):
            if all(
                xor_across_sep_row(ex["input"], paint, sep_color) == ex["output"]
                for ex in train
            ):
                return paint, sep_color
    return None


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    params = _learn_params(train)
    if params is None:
        return []
    paint, sep_color = params

    def _xf(grid: Grid) -> Optional[Grid]:
        return xor_across_sep_row(grid, paint, sep_color)

    return [(f"xor_sep_row_paint{paint}_sep{sep_color}", _xf)]

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
            "engine": "s1_xor_across_sep_row",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_xor_across_sep_row",
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
    "xor_across_sep_row",
]
