"""S2 small-component recolor-to-3 (FoT).

Grammar (same_canvas_rewrite):
  Partition the input into 4-connected same-color components (zeros ignored).
  Every component whose cell count is ≤ 2 is recolored to 3; larger components
  are left unchanged. Licensed only on perfect train replay.

Canonical close: AGI-2 test task 12eac192.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_PAINT = 3
_MAX_SMALL = 2


def _components(g: Grid) -> List[Tuple[int, List[Tuple[int, int]]]]:
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    out: List[Tuple[int, List[Tuple[int, int]]]] = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or g[r][c] == 0:
                continue
            col = g[r][c]
            cells: List[Tuple[int, int]] = []
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and g[nr][nc] == col:
                        seen[nr][nc] = True
                        q.append((nr, nc))
            out.append((col, cells))
    return out


def _recolor_small(inp: Grid, paint: int = _PAINT, max_small: int = _MAX_SMALL) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    out = [row[:] for row in inp]
    for _col, cells in _components(inp):
        if len(cells) <= max_small:
            for r, c in cells:
                out[r][c] = paint
    return out


def make_small_comp_recolor3() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _recolor_small(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("small_comp_recolor3", make_small_comp_recolor3())]


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
            "engine": "s2_small_comp_recolor3",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_small_comp_recolor3",
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
