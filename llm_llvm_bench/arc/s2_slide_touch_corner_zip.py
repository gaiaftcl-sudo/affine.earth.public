"""S2 slide-to-touch with far-corner zip (FoT).

Grammar (same_canvas_rewrite):
  Background 7, mover color 2, target color 5. Slide the 2-block toward the
  5-block along the axis with positive gap until they touch. Then zip: move the
  far corner of the 5-block one step around the contact (direction-specific):
    right (2 left of 5): top-right 5 -> one above
    down  (2 above 5):   bottom-right 5 -> one below bottom-left
    up    (2 below 5):   top-right 5 -> one above-left of top-left
    left  (2 right of 5): top-left 5 -> one above

Canonical close: AGI-2 test task 11dc524f.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_slide_touch_corner_zip(
    bg: int = 7, mover: int = 2, target: int = 5
) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        A = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == mover]
        B = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == target]
        if not A or not B:
            return None
        ar0, ar1 = min(r for r, _ in A), max(r for r, _ in A)
        ac0, ac1 = min(c for _, c in A), max(c for _, c in A)
        br0, br1 = min(r for r, _ in B), max(r for r, _ in B)
        bc0, bc1 = min(c for _, c in B), max(c for _, c in B)
        cands: List[Tuple[int, int, int, str]] = []
        if ac1 < bc0:
            cands.append((0, 1, bc0 - ac1 - 1, "right"))
        if ar1 < br0:
            cands.append((1, 0, br0 - ar1 - 1, "down"))
        if bc1 < ac0:
            cands.append((0, -1, ac0 - bc1 - 1, "left"))
        if br1 < ar0:
            cands.append((-1, 0, ar0 - br1 - 1, "up"))
        if not cands:
            return None
        dr, dc, shift, kind = max(cands, key=lambda x: x[2])
        A2 = [(r + dr * shift, c + dc * shift) for r, c in A]
        if any(not (0 <= r < h and 0 <= c < w) for r, c in A2):
            return None
        B2 = list(B)
        if kind == "right":
            src, dst = (br0, bc1), (br0 - 1, bc1)
        elif kind == "left":
            src, dst = (br0, bc0), (br0 - 1, bc0)
        elif kind == "down":
            src, dst = (br1, bc1), (br1 + 1, bc0)
        else:
            src, dst = (br0, bc1), (br0 - 1, bc0 - 1)
        if src in B2:
            B2.remove(src)
            if 0 <= dst[0] < h and 0 <= dst[1] < w:
                B2.append(dst)
            else:
                return None
        out = [[bg] * w for _ in range(h)]
        for r, c in A2:
            out[r][c] = mover
        for r, c in B2:
            out[r][c] = target
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("slide_touch_corner_zip", make_slide_touch_corner_zip())]


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
            "engine": "s2_slide_touch_corner_zip",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_slide_touch_corner_zip",
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
