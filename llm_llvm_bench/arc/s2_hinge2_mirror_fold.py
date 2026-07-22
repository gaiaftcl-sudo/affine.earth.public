"""S2 hinge-2 mirror fold (FoT).

Grammar (same_canvas_rewrite):
  Non-zero palette has a hinge color 2 and one body color. Fold the body across
  the mid-axis between the facing body edge and the facing hinge edge
  (horizontal if hinge is left/right of body, else vertical). Recolor hinge
  cells to body. Fill remaining canvas with 3.

Canonical close: AGI-2 test task 2bcee788.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_hinge2_mirror_fold(hinge: int = 2, fill: int = 3) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        cells = [(r, c, inp[r][c]) for r in range(h) for c in range(w) if inp[r][c] != 0]
        if not cells:
            return None
        cols = Counter(v for _, _, v in cells)
        if hinge not in cols or len(cols) < 2:
            return None
        body_colors = [c for c in cols if c != hinge]
        if len(body_colors) != 1:
            return None
        body = body_colors[0]
        hinge_cells = [(r, c) for r, c, v in cells if v == hinge]
        body_cells = [(r, c) for r, c, v in cells if v == body]
        if not hinge_cells or not body_cells:
            return None
        br = sum(r for r, _ in body_cells) / len(body_cells)
        bc = sum(c for _, c in body_cells) / len(body_cells)
        hr = sum(r for r, _ in hinge_cells) / len(hinge_cells)
        hc = sum(c for _, c in hinge_cells) / len(hinge_cells)
        out = [[fill] * w for _ in range(h)]
        for r, c in body_cells:
            out[r][c] = body
        for r, c in hinge_cells:
            out[r][c] = body
        if abs(hc - bc) >= abs(hr - br):
            if hc >= bc:
                axis = (
                    max(c for _, c in body_cells) + min(c for _, c in hinge_cells)
                ) / 2
            else:
                axis = (
                    min(c for _, c in body_cells) + max(c for _, c in hinge_cells)
                ) / 2
            for r, c in body_cells:
                nc = int(round(2 * axis - c))
                if 0 <= nc < w:
                    out[r][nc] = body
        else:
            if hr >= br:
                axis = (
                    max(r for r, _ in body_cells) + min(r for r, _ in hinge_cells)
                ) / 2
            else:
                axis = (
                    min(r for r, _ in body_cells) + max(r for r, _ in hinge_cells)
                ) / 2
            for r, c in body_cells:
                nr = int(round(2 * axis - r))
                if 0 <= nr < h:
                    out[nr][c] = body
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("hinge2_mirror_fold", make_hinge2_mirror_fold())]


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
            "engine": "s2_hinge2_mirror_fold",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_hinge2_mirror_fold",
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
