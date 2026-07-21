"""S1 most-common shape 8-connected (FoT).

Grammar (zoom_in_crop):
  8-connected components with size≥2; pick the translation-normalized shape
  that appears most often; emit one exemplar in its bbox.

Canonical close: AGI-2 test task 39a8645d.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Shape = frozenset


def _comps8(g: Grid) -> List[Tuple[int, List[Tuple[int, int]]]]:
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
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
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


def _normalize(cells: Sequence[Tuple[int, int]]) -> Shape:
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _extract(inp: Grid) -> Optional[Grid]:
    by_shape: Counter = Counter()
    exemplars: Dict[Shape, Tuple[int, List[Tuple[int, int]]]] = {}
    for v, cells in _comps8(inp):
        if len(cells) < 2:
            continue
        sh = _normalize(cells)
        by_shape[sh] += 1
        exemplars[sh] = (v, cells)
    if not by_shape:
        return None
    sh = max(by_shape.items(), key=lambda t: t[1])[0]
    v, cells = exemplars[sh]
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    s = set(cells)
    return [[v if (r, c) in s else 0 for c in range(c1, c2 + 1)] for r in range(r1, r2 + 1)]


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("most_common_shape_8conn", _extract)]


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
            "engine": "s1_most_common_shape_8conn",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_most_common_shape_8conn",
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
