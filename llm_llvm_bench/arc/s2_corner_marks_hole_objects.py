"""S2 corner-marks on holed objects (FoT).

Grammar (same_canvas_rewrite):
  Background = modal color. Object = modal non-background color.
  Select every object component that encloses a hole, plus any object
  components nested inside those holes. On each selected component, mark
  orthogonal exterior corner adjacencies with border color 2 (bg cells only).

Canonical close: AGI-2 test task 14b8e18c.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]


def _components(grid: Grid, color: int) -> List[List[Cell]]:
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps: List[List[Cell]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or seen[r][c]:
                continue
            stack = [(r, c)]
            cells: List[Cell] = []
            seen[r][c] = True
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and not seen[nx][ny]
                        and grid[nx][ny] == color
                    ):
                        seen[nx][ny] = True
                        stack.append((nx, ny))
            comps.append(cells)
    return comps


def _enclosed_cells(inp: Grid, cells: Sequence[Cell]) -> Set[Cell]:
    cellset = set(cells)
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    stack: List[Cell] = []
    for r in range(r0, r1 + 1):
        for c in (c0, c1):
            if (r, c) not in cellset:
                stack.append((r, c))
    for c in range(c0, c1 + 1):
        for r in (r0, r1):
            if (r, c) not in cellset:
                stack.append((r, c))
    seen: Set[Cell] = set()
    while stack:
        r, c = stack.pop()
        if (r, c) in seen:
            continue
        if not (r0 <= r <= r1 and c0 <= c <= c1):
            continue
        if (r, c) in cellset:
            continue
        seen.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            stack.append((r + dr, c + dc))
    enc: Set[Cell] = set()
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if (r, c) not in cellset and (r, c) not in seen:
                enc.add((r, c))
    return enc


def _has_hole(inp: Grid, cells: Sequence[Cell], bg: int) -> bool:
    return any(inp[r][c] == bg for r, c in _enclosed_cells(inp, cells))


def make_corner_marks_hole_objects(border: int = 2) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        flat = [v for row in inp for v in row]
        bg = Counter(flat).most_common(1)[0][0]
        others = [v for v, _ in Counter(flat).most_common() if v != bg]
        if not others:
            return None
        obj = others[0]
        comps = _components(inp, obj)
        if not comps:
            return None
        chosen: List[List[Cell]] = []
        for comp in comps:
            if _has_hole(inp, comp, bg):
                chosen.append(comp)
                enc = _enclosed_cells(inp, comp)
                for other in comps:
                    if other is comp:
                        continue
                    if any(cell in enc for cell in other):
                        chosen.append(other)
        if not chosen:
            chosen = [max(comps, key=len)]
        seen_ids: Set[int] = set()
        uniq: List[List[Cell]] = []
        for comp in chosen:
            cid = id(comp)
            if cid in seen_ids:
                continue
            seen_ids.add(cid)
            uniq.append(comp)
        h, w = len(inp), len(inp[0])
        out = [list(row) for row in inp]
        pairs = (
            ((-1, 0), (0, -1)),
            ((-1, 0), (0, 1)),
            ((1, 0), (0, -1)),
            ((1, 0), (0, 1)),
        )
        for comp in uniq:
            cells = set(comp)
            for r, c in cells:
                for d1, d2 in pairs:
                    n1 = (r + d1[0], c + d1[1])
                    n2 = (r + d2[0], c + d2[1])

                    def exterior(p: Cell) -> bool:
                        rr, cc = p
                        if not (0 <= rr < h and 0 <= cc < w):
                            return True
                        return (rr, cc) not in cells

                    if exterior(n1) and exterior(n2):
                        for rr, cc in (n1, n2):
                            if 0 <= rr < h and 0 <= cc < w and out[rr][cc] == bg:
                                out[rr][cc] = border
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("corner_marks_hole_objects", make_corner_marks_hole_objects())]


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
            "engine": "s2_corner_marks_hole_objects",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_corner_marks_hole_objects",
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
