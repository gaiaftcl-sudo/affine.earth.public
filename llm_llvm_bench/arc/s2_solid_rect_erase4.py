"""S2 solid-rectangle erase-to-4 (FoT).

Grammar (same_canvas_rewrite):
  Find maximal axis-aligned solid rectangles (every cell the same color).
  Any such rectangle whose area is ≥ 25 is recolored to 4. Smaller / non-solid
  noise regions are left unchanged. Licensed only on perfect train replay.

Canonical close: AGI-2 test task 25094a63.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_FILL = 4
_MIN_AREA = 25


def _solid_rects(inp: Grid, min_area: int) -> List[Tuple[int, int, int, int, int]]:
    """Return maximal solid rects as (r0, r1, c0, c1, color)."""
    h, w = len(inp), len(inp[0])
    found: List[Tuple[int, int, int, int, int, int]] = []
    for r0 in range(h):
        for r1 in range(r0, h):
            ok_cols = [
                all(inp[r][c] == inp[r0][c] for r in range(r0, r1 + 1)) for c in range(w)
            ]
            c = 0
            while c < w:
                if not ok_cols[c]:
                    c += 1
                    continue
                col = inp[r0][c]
                c0 = c
                while c < w and ok_cols[c] and inp[r0][c] == col:
                    c += 1
                c1 = c - 1
                area = (r1 - r0 + 1) * (c1 - c0 + 1)
                if area >= min_area:
                    found.append((area, r0, r1, c0, c1, col))
    found = sorted(set(found), reverse=True)
    maximal: List[Tuple[int, int, int, int, int]] = []
    for area, r0, r1, c0, c1, col in found:
        if any(
            R0 <= r0 and r1 <= R1 and C0 <= c0 and c1 <= C1
            for (R0, R1, C0, C1, _) in maximal
        ):
            continue
        maximal = [
            m
            for m in maximal
            if not (r0 <= m[0] and m[1] <= r1 and c0 <= m[2] and m[3] <= c1)
        ]
        maximal.append((r0, r1, c0, c1, col))
    return maximal


def _apply(inp: Grid, fill: int = _FILL, min_area: int = _MIN_AREA) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    out = [row[:] for row in inp]
    changed = False
    for r0, r1, c0, c1, col in _solid_rects(inp, min_area):
        if col == fill:
            continue
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if out[r][c] != fill:
                    out[r][c] = fill
                    changed = True
    return out if changed else None


def make_solid_rect_erase4() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _apply(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("solid_rect_erase4", make_solid_rect_erase4())]


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
            "engine": "s2_solid_rect_erase4",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_solid_rect_erase4",
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
