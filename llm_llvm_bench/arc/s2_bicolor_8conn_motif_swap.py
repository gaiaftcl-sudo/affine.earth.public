"""S2 bicolor 8-conn motif swap (FoT).

Grammar (same_canvas_rewrite):
  Exactly two non-background colors A and B. Take 8-connected components of
  each. The template for a color is its most common component shape (normalized
  to the component bbox origin). At every A-component origin, stamp B's
  template in color B; at every B-component origin, stamp A's template in
  color A.

Canonical close: AGI-2 test task 3391f8c0.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]


def _comps8(inp: Grid, col: int, bg: int = 0) -> List[List[Cell]]:
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    out: List[List[Cell]] = []
    for r in range(h):
        for c in range(w):
            if inp[r][c] != col or seen[r][c]:
                continue
            q = deque([(r, c)])
            seen[r][c] = True
            cells: List[Cell] = []
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
                            and inp[nx][ny] == col
                        ):
                            seen[nx][ny] = True
                            q.append((nx, ny))
            out.append(cells)
    return out


def _shape_rel(cells: Sequence[Cell]) -> frozenset:
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _pick_template(comps: Sequence[Sequence[Cell]]) -> frozenset:
    shapes = [_shape_rel(c) for c in comps]
    return Counter(shapes).most_common(1)[0][0]


def make_bicolor_8conn_motif_swap(bg: int = 0) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        cols = sorted({v for row in inp for v in row if v != bg})
        if len(cols) != 2:
            return None
        a, b = cols
        ca, cb = _comps8(inp, a, bg), _comps8(inp, b, bg)
        if not ca or not cb:
            return None
        rela, relb = _pick_template(ca), _pick_template(cb)
        out = [[bg] * w for _ in range(h)]
        for cells in ca:
            r0 = min(r for r, _ in cells)
            c0 = min(c for _, c in cells)
            for dr, dc in relb:
                rr, cc = r0 + dr, c0 + dc
                if 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = b
        for cells in cb:
            r0 = min(r for r, _ in cells)
            c0 = min(c for _, c in cells)
            for dr, dc in rela:
                rr, cc = r0 + dr, c0 + dc
                if 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = a
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("bicolor_8conn_motif_swap", make_bicolor_8conn_motif_swap())]


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
            "engine": "s2_bicolor_8conn_motif_swap",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_bicolor_8conn_motif_swap",
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
