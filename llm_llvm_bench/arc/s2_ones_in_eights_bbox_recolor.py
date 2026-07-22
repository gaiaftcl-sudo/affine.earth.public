"""S2 ones inside eights-bbox touch-recolor (FoT).

Grammar (same_canvas_rewrite):
  Compute the axis-aligned bounding box of all color-8 cells. Every color-1
  cell inside that box that touches an 8 in 8-connectivity is recolored to 3.

Canonical close: AGI-2 test task 32597951.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_ones_in_eights_bbox_recolor(
    src: int = 1, dst: int = 3, touch: int = 8
) -> Transform:
    neigh = (
        (0, 1),
        (0, -1),
        (1, 0),
        (-1, 0),
        (1, 1),
        (1, -1),
        (-1, 1),
        (-1, -1),
    )

    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        eights = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == touch]
        if not eights:
            return None
        r0 = min(r for r, _ in eights)
        r1 = max(r for r, _ in eights)
        c0 = min(c for _, c in eights)
        c1 = max(c for _, c in eights)
        out = [list(row) for row in inp]
        hit = False
        for r in range(h):
            for c in range(w):
                if inp[r][c] != src:
                    continue
                if not (r0 <= r <= r1 and c0 <= c <= c1):
                    continue
                if any(
                    0 <= r + dr < h
                    and 0 <= c + dc < w
                    and inp[r + dr][c + dc] == touch
                    for dr, dc in neigh
                ):
                    out[r][c] = dst
                    hit = True
        return out if hit else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("ones_in_eights_bbox_recolor", make_ones_in_eights_bbox_recolor())]


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
            "engine": "s2_ones_in_eights_bbox_recolor",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_ones_in_eights_bbox_recolor",
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
