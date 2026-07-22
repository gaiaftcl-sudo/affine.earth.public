"""S2 marker pure-diagonal border (FoT).

Grammar (same_canvas_rewrite):
  Background 7. Two foreground colors: object (majority) and marker (minority,
  already placed inside the object). Paint marker onto every background cell
  that is diagonally adjacent to the object∪marker body but not orthogonally
  adjacent to it (pure diagonal corners / knight-free diagonal ring).

Canonical close: AGI-2 test task 396d80d7.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_marker_pure_diag_border(bg: int = 7) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        cnt = Counter(v for row in inp for v in row if v != bg)
        if len(cnt) != 2:
            return None
        marker = min(cnt.items(), key=lambda x: x[1])[0]
        obj = [c for c in cnt if c != marker][0]
        body = {
            (r, c)
            for r in range(h)
            for c in range(w)
            if inp[r][c] in (obj, marker)
        }
        if not body:
            return None
        out = [row[:] for row in inp]
        painted = False
        for r in range(h):
            for c in range(w):
                if inp[r][c] != bg:
                    continue
                diag = any(
                    (r + dr, c + dc) in body
                    for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1))
                )
                ortho = any(
                    (r + dr, c + dc) in body
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                )
                if diag and not ortho:
                    out[r][c] = marker
                    painted = True
        if not painted:
            return None
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("marker_pure_diag_border", make_marker_pure_diag_border())]


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
            "engine": "s2_marker_pure_diag_border",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_marker_pure_diag_border",
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
