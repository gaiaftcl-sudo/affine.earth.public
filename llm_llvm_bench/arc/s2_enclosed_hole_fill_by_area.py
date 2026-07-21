"""S2 enclosed-hole fill by area (FoT).

Grammar (same_canvas_rewrite):
  Find 4-connected zero components that do not touch the border
  (holes enclosed by nonzero walls). Learn a stable area→fill-color
  map from train demos; apply that map to every hole.

Canonical close: AGI-2 test task 00dbd492.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def enclosed_holes(inp: Grid, min_area: int = 2) -> List[List[Tuple[int, int]]]:
    if not inp or not inp[0]:
        return []
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    holes: List[List[Tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if inp[r][c] != 0 or seen[r][c]:
                continue
            q = deque([(r, c)])
            seen[r][c] = True
            cells: List[Tuple[int, int]] = []
            border = False
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                if x in (0, h - 1) or y in (0, w - 1):
                    border = True
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < h and 0 <= ny < w and not seen[nx][ny] and inp[nx][ny] == 0:
                        seen[nx][ny] = True
                        q.append((nx, ny))
            if not border and len(cells) >= min_area:
                holes.append(cells)
    return holes


def _learn_area_map(train: Sequence[Dict[str, Any]]) -> Optional[Dict[int, int]]:
    mapping: Dict[int, int] = {}
    for example in train:
        gi = example["input"]
        go = example["output"]
        if len(gi) != len(go) or (gi and go and len(gi[0]) != len(go[0])):
            return None
        for cells in enclosed_holes(gi):
            colors = {go[r][c] for r, c in cells}
            if len(colors) != 1:
                return None
            col = next(iter(colors))
            if col == 0:
                return None
            area = len(cells)
            if area in mapping and mapping[area] != col:
                return None
            mapping[area] = col
    return mapping or None


def make_hole_fill(mapping: Dict[int, int]) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        out = [list(row) for row in inp]
        for cells in enclosed_holes(inp):
            col = mapping.get(len(cells))
            if col is None:
                return None
            for r, c in cells:
                out[r][c] = col
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    mapping = _learn_area_map(train)
    if mapping is None:
        return []
    return [("enclosed_hole_fill_by_area", make_hole_fill(mapping))]


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
            "engine": "s2_enclosed_hole_fill_by_area",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_enclosed_hole_fill_by_area",
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
    "enclosed_holes",
    "exact_candidates",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
