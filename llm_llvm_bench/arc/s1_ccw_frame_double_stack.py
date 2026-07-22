"""S1 CCW rotate + rail frame + double stack (FoT).

Grammar (zoom_out_expand):
  Rotate the grid 90° counter-clockwise. Wrap with side rails of 1 and
  top/bottom border rows `7 + 1×W + 7`. Stack that panel twice, sharing the
  middle border rail.

Canonical close: AGI-2 test task 412b6263.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _ccw(g: Grid) -> Grid:
    return [list(row) for row in zip(*g)][::-1]


def ccw_frame_double_stack(
    inp: Grid, border: int = 7, rail: int = 1
) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    g = _ccw(inp)
    h, w = len(g), len(g[0])
    panel: Grid = []
    panel.append([border] + [rail] * w + [border])
    for row in g:
        panel.append([rail] + list(row) + [rail])
    panel.append([border] + [rail] * w + [border])
    return panel + panel[1:]


def make_ccw_frame_double_stack() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return ccw_frame_double_stack(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("ccw_frame_double_stack", make_ccw_frame_double_stack())]


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
            "engine": "s1_ccw_frame_double_stack",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_ccw_frame_double_stack",
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
    "ccw_frame_double_stack",
    "exact_candidates",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
