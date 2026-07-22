"""S2 color-directed translate (FoT).

Grammar (same_canvas_rewrite):
  For each non-background color, learn a uniform (dr, dc) translation from the
  train demos (same color must move by the same vector on every demo where it
  appears). Apply those translations on the test grid.

Canonical close: AGI-2 test task 342dd610.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _bg(grid: Grid) -> int:
    return Counter(v for row in grid for v in row).most_common(1)[0][0]


def _cells(grid: Grid, col: int) -> List[Tuple[int, int]]:
    return [
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == col
    ]


def _learn_translations(
    train: Sequence[Dict[str, Any]],
) -> Optional[Dict[int, Tuple[int, int]]]:
    mapping: Dict[int, Tuple[int, int]] = {}
    for ex in train:
        inp, out = ex["input"], ex["output"]
        if len(inp) != len(out) or len(inp[0]) != len(out[0]):
            return None
        bg = _bg(inp)
        colors = {v for row in inp for v in row if v != bg}
        for col in colors:
            cin = sorted(_cells(inp, col))
            cout = sorted(_cells(out, col))
            if not cin or len(cin) != len(cout):
                return None
            cy = sum(r for r, _ in cin) / len(cin)
            cx = sum(c for _, c in cin) / len(cin)
            dy = sum(r for r, _ in cout) / len(cout) - cy
            dx = sum(c for _, c in cout) / len(cout) - cx
            dr, dc = int(round(dy)), int(round(dx))
            moved = sorted((r + dr, c + dc) for r, c in cin)
            if moved != cout:
                return None
            if col in mapping and mapping[col] != (dr, dc):
                return None
            mapping[col] = (dr, dc)
    return mapping or None


def make_color_directed_translate(train: Sequence[Dict[str, Any]]) -> Transform:
    mapping = _learn_translations(train)

    def transform(inp: Grid) -> Optional[Grid]:
        if mapping is None or not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        bg = _bg(inp)
        out = [list(row) for row in inp]
        by_col: Dict[int, List[Tuple[int, int]]] = {}
        for r in range(h):
            for c in range(w):
                v = inp[r][c]
                if v != bg:
                    by_col.setdefault(v, []).append((r, c))
        for col, cells in by_col.items():
            if col not in mapping:
                return None
            dr, dc = mapping[col]
            for r, c in cells:
                out[r][c] = bg
            for r, c in cells:
                rr, cc = r + dr, c + dc
                if not (0 <= rr < h and 0 <= cc < w):
                    return None
                out[rr][cc] = col
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("color_directed_translate", make_color_directed_translate(train))]


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
            "engine": "s2_color_directed_translate",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_color_directed_translate",
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
