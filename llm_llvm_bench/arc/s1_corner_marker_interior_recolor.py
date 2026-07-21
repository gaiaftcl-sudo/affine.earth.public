"""S1 corner-marker interior recolor (FoT).

Grammar (zoom_in_crop):
  Marker color appears as 2 or 4 singleton cells. Crop the exclusive interior
  of their axis-aligned bbox; recolor every nonzero non-marker cell to marker.

Canonical close: AGI-2 test task 3de23699.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _comps(g: Grid) -> List[Tuple[int, List[Tuple[int, int]]]]:
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    out: List[Tuple[int, List[Tuple[int, int]]]] = []
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0 or seen[r][c]:
                continue
            v = g[r][c]
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
                        and g[nx][ny] == v
                    ):
                        seen[nx][ny] = True
                        q.append((nx, ny))
            out.append((v, cells))
    return out


def _transform(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    nz = Counter(c for row in inp for c in row if c)
    marker = None
    for col, n in nz.items():
        cs = [cells for v, cells in _comps(inp) if v == col]
        if n in (2, 4) and cs and all(len(cells) == 1 for cells in cs):
            marker = col
            break
    if marker is None:
        return None
    marks = [
        (r, c)
        for r in range(len(inp))
        for c in range(len(inp[0]))
        if inp[r][c] == marker
    ]
    if len(marks) < 2:
        return None
    r1 = min(r for r, _ in marks)
    r2 = max(r for r, _ in marks)
    c1 = min(c for _, c in marks)
    c2 = max(c for _, c in marks)
    if r2 - r1 < 2 or c2 - c1 < 2:
        return None
    out: Grid = []
    for r in range(r1 + 1, r2):
        row: List[int] = []
        for c in range(c1 + 1, c2):
            v = inp[r][c]
            row.append(marker if v != 0 and v != marker else 0)
        out.append(row)
    return out if out and out[0] else None


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("corner_marker_interior_recolor", _transform)]


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
            "engine": "s1_corner_marker_interior_recolor",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_corner_marker_interior_recolor",
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
