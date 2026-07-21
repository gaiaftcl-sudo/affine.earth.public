"""S2 three-point star path (FoT).

Grammar (same_canvas_rewrite):
  Exactly three nonzero marker cells with distinct colors. Sort markers
  by color ascending. Connect each of the two lower-color markers to the
  highest-color marker with a rectilinear elbow path, filling open cells
  with a learned path color. Elbow polarity per edge is learned from
  train (two binary choices per edge).

Canonical close: AGI-2 test task 0e671a1a.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from itertools import product
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Point = Tuple[int, int]


def _markers(inp: Grid) -> List[Tuple[int, int, int]]:
    pts = [(r, c, inp[r][c]) for r in range(len(inp)) for c in range(len(inp[0])) if inp[r][c]]
    pts.sort(key=lambda x: x[2])
    return pts


def _elbows(a: Point, b: Point) -> Tuple[List[Point], List[Point]]:
    (r1, c1), (r2, c2) = a, b

    def uniq(path: List[Point]) -> List[Point]:
        seen = set()
        out: List[Point] = []
        for p in path:
            if p in seen:
                continue
            seen.add(p)
            out.append(p)
        return out

    p1: List[Point] = []
    for c in range(min(c1, c2), max(c1, c2) + 1):
        p1.append((r1, c))
    for r in range(min(r1, r2), max(r1, r2) + 1):
        p1.append((r, c2))
    p2: List[Point] = []
    for r in range(min(r1, r2), max(r1, r2) + 1):
        p2.append((r, c1))
    for c in range(min(c1, c2), max(c1, c2) + 1):
        p2.append((r2, c))
    return uniq(p1), uniq(p2)


def _apply(inp: Grid, paths: Sequence[Sequence[Point]], fill: int) -> Grid:
    out = [list(row) for row in inp]
    for path in paths:
        for r, c in path:
            if out[r][c] == 0:
                out[r][c] = fill
    return out


def _path_color(train: Sequence[Dict[str, Any]]) -> Optional[int]:
    colors = set()
    for example in train:
        gin = {c for row in example["input"] for c in row}
        gout = {c for row in example["output"] for c in row}
        added = gout - gin
        added.discard(0)
        if len(added) != 1:
            return None
        colors.add(next(iter(added)))
    if len(colors) != 1:
        return None
    return next(iter(colors))


def _learn(train: Sequence[Dict[str, Any]]) -> Optional[Tuple[int, Tuple[int, int]]]:
    fill = _path_color(train)
    if fill is None:
        return None
    # Star centered on highest-color marker (index 2): edges (0,2), (1,2).
    common: Optional[set] = None
    for example in train:
        gi = example["input"]
        go = example["output"]
        pts = _markers(gi)
        if len(pts) != 3 or len({p[2] for p in pts}) != 3:
            return None
        if len(gi) != len(go) or len(gi[0]) != len(go[0]):
            return None
        coords = [(r, c) for r, c, _ in pts]
        good = set()
        e0 = _elbows(coords[0], coords[2])
        e1 = _elbows(coords[1], coords[2])
        for choice in product((0, 1), repeat=2):
            paths = [e0[choice[0]], e1[choice[1]]]
            if _apply(gi, paths, fill) == go:
                good.add(choice)
        if not good:
            return None
        common = good if common is None else common & good
    if not common or len(common) != 1:
        return None
    return fill, next(iter(common))


def make_star(fill: int, choice: Tuple[int, int]) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        pts = _markers(inp)
        if len(pts) != 3 or len({p[2] for p in pts}) != 3:
            return None
        coords = [(r, c) for r, c, _ in pts]
        e0 = _elbows(coords[0], coords[2])
        e1 = _elbows(coords[1], coords[2])
        paths = [e0[choice[0]], e1[choice[1]]]
        return _apply(inp, paths, fill)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    learned = _learn(train)
    if learned is None:
        return []
    fill, choice = learned
    return [("three_point_star_path", make_star(fill, choice))]


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
            "engine": "s2_three_point_star_path",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_three_point_star_path",
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
