"""S2 marker paint block edge (FoT).

Grammar (same_canvas_rewrite):
  Largest nonzero component is the block. Each singleton marker outside
  the block paints the nearest axis-aligned edge cell of the block's
  bounding box (clamped onto that edge).

Canonical close: AGI-2 test task 1f642eb9.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Point = Tuple[int, int]


def _components(inp: Grid) -> List[Tuple[int, List[Point]]]:
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    out: List[Tuple[int, List[Point]]] = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or inp[r][c] == 0:
                continue
            col = inp[r][c]
            q = deque([(r, c)])
            seen[r][c] = True
            cells: List[Point] = []
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < h and 0 <= ny < w and not seen[nx][ny] and inp[nx][ny] == col:
                        seen[nx][ny] = True
                        q.append((nx, ny))
            out.append((col, cells))
    return out


def marker_paint_block_edge(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    comps = _components(inp)
    if not comps:
        return None
    bcol, bcells = max(comps, key=lambda x: len(x[1]))
    if len(bcells) < 4:
        return None
    rs = [r for r, _ in bcells]
    cs = [c for _, c in bcells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    block: Set[Point] = set(bcells)
    out = [list(row) for row in inp]
    for col, cells in comps:
        if col == bcol or len(cells) != 1:
            continue
        mr, mc = cells[0]
        if mr < r0:
            tr, tc = r0, max(c0, min(c1, mc))
        elif mr > r1:
            tr, tc = r1, max(c0, min(c1, mc))
        elif mc < c0:
            tr, tc = max(r0, min(r1, mr)), c0
        elif mc > c1:
            tr, tc = max(r0, min(r1, mr)), c1
        else:
            continue
        if (tr, tc) in block or out[tr][tc] == bcol:
            out[tr][tc] = col
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("marker_paint_block_edge", marker_paint_block_edge)]


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
            "engine": "s2_marker_paint_block_edge",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_marker_paint_block_edge",
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
    "marker_paint_block_edge",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
