"""S2 same-color diagonal bridges (FoT).

Grammar (same_canvas_rewrite):
  Background is the majority color. For each non-background color, take its
  4-connected components. Between every pair of components, if the nearest
  cell pair (Manhattan) lies on a pure diagonal (|dr|==|dc|>1), paint the
  open diagonal steps between them with that color.

Canonical close: AGI-2 test task 342ae2ed.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]


def _components(cells: Sequence[Cell]) -> List[List[Cell]]:
    cell_set = set(cells)
    seen: set[Cell] = set()
    comps: List[List[Cell]] = []
    for cell in cells:
        if cell in seen:
            continue
        q = deque([cell])
        seen.add(cell)
        comp: List[Cell] = []
        while q:
            r, c = q.popleft()
            comp.append((r, c))
            for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nxt = (r + dr, c + dc)
                if nxt in cell_set and nxt not in seen:
                    seen.add(nxt)
                    q.append(nxt)
        comps.append(comp)
    return comps


def make_same_color_diag_bridge() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        bg = Counter(v for row in inp for v in row).most_common(1)[0][0]
        out = [list(row) for row in inp]
        painted = False
        colors = sorted({v for row in inp for v in row if v != bg})
        for color in colors:
            cells = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == color]
            comps = _components(cells)
            if len(comps) < 2:
                continue
            for i in range(len(comps)):
                for j in range(i + 1, len(comps)):
                    best: Optional[Tuple[Cell, Cell]] = None
                    best_d = 10**9
                    for a in comps[i]:
                        for b in comps[j]:
                            d = abs(a[0] - b[0]) + abs(a[1] - b[1])
                            if d < best_d:
                                best_d = d
                                best = (a, b)
                    if best is None:
                        continue
                    (r1, c1), (r2, c2) = best
                    if abs(r2 - r1) != abs(c2 - c1) or abs(r2 - r1) <= 1:
                        continue
                    dr = 1 if r2 > r1 else -1
                    dc = 1 if c2 > c1 else -1
                    r, c = r1 + dr, c1 + dc
                    ok = True
                    steps: List[Cell] = []
                    while (r, c) != (r2, c2):
                        if not (0 <= r < h and 0 <= c < w):
                            ok = False
                            break
                        if inp[r][c] != bg:
                            ok = False
                            break
                        steps.append((r, c))
                        r += dr
                        c += dc
                    if not ok or not steps:
                        continue
                    for rr, cc in steps:
                        out[rr][cc] = color
                        painted = True
        if not painted:
            return None
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("same_color_diag_bridge", make_same_color_diag_bridge())]


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
            "engine": "s2_same_color_diag_bridge",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_same_color_diag_bridge",
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
