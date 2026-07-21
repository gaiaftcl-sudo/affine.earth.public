"""S2 ones-shape template recolor (FoT).

Grammar (same_canvas_rewrite):
  Each 4-connected component of color 1 is recolored to the color of the
  unique non-1 template component with the same translation-normalized shape.

Canonical close: AGI-2 test task 2a5f8217.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Shape = frozenset


def _normalize(cells: Sequence[Tuple[int, int]]) -> Shape:
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _components(g: Grid) -> List[Tuple[int, List[Tuple[int, int]], Shape]]:
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    comps: List[Tuple[int, List[Tuple[int, int]], Shape]] = []
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0 or seen[r][c]:
                continue
            col = g[r][c]
            q = deque([(r, c)])
            seen[r][c] = True
            cells: List[Tuple[int, int]] = []
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and not seen[nx][ny]
                        and g[nx][ny] == col
                    ):
                        seen[nx][ny] = True
                        q.append((nx, ny))
            comps.append((col, cells, _normalize(cells)))
    return comps


def _recolor(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    comps = _components(inp)
    templates: Dict[Shape, int] = {}
    ones: List[Tuple[List[Tuple[int, int]], Shape]] = []
    for col, cells, shape in comps:
        if col == 1:
            ones.append((cells, shape))
        else:
            if shape in templates and templates[shape] != col:
                return None
            templates[shape] = col
    if not ones or not templates:
        return None
    out = [list(row) for row in inp]
    for cells, shape in ones:
        if shape not in templates:
            return None
        tc = templates[shape]
        for r, c in cells:
            out[r][c] = tc
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("ones_shape_template_recolor", _recolor)]


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
            "engine": "s2_ones_shape_template_recolor",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_ones_shape_template_recolor",
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
    "exact_candidates",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
