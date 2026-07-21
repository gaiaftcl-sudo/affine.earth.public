"""S2 marker-3 template stamp (FoT).

Grammar (same_canvas_rewrite):
  For each cell colored 3, stamp a fixed local template (5-crown, 2-pillars,
  8-bar). Then on each template's bar row (marker_row+2), fill remaining
  zeros with 2 across the full canvas width.

Canonical close: AGI-2 test task 3f23242b.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_LOCAL = [
    (-2, -2, 5),
    (-2, -1, 5),
    (-2, 0, 5),
    (-2, 1, 5),
    (-2, 2, 5),
    (-1, -2, 2),
    (-1, 0, 5),
    (-1, 2, 2),
    (0, -2, 2),
    (0, 0, 3),
    (0, 2, 2),
    (1, -2, 2),
    (1, 2, 2),
    (2, -2, 8),
    (2, -1, 8),
    (2, 0, 8),
    (2, 1, 8),
    (2, 2, 8),
]


def make_stamp(marker: int = 3, bar_fill: int = 2) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        marks = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == marker]
        if not marks:
            return None
        out = [[0] * w for _ in range(h)]
        bar_rows = set()
        for mr, mc in marks:
            for dr, dc, v in _LOCAL:
                nr, nc = mr + dr, mc + dc
                if 0 <= nr < h and 0 <= nc < w:
                    out[nr][nc] = v
            bar_rows.add(mr + 2)
        for br in bar_rows:
            if 0 <= br < h:
                for c in range(w):
                    if out[br][c] == 0:
                        out[br][c] = bar_fill
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("marker3_template_stamp", make_stamp())]


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
            "engine": "s2_marker3_template_stamp",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_marker3_template_stamp",
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
