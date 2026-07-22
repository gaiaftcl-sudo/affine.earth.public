"""S2 ink sealed/open side-dock (FoT).

Grammar (same_canvas_rewrite):
  Background is the majority color; ink is the other color. Each 4-connected
  ink component keeps its rows and docks rigidly to the left edge (recolor 2)
  when it is perimeter-sealed or has enclosed background holes; otherwise it
  docks to the right edge (recolor 3). Licensed only on perfect train replay.

Canonical close: AGI-2 test task 320afe60.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _components(inp: Grid, color: int) -> List[List[Tuple[int, int]]]:
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    comps: List[List[Tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or inp[r][c] != color:
                continue
            cells: List[Tuple[int, int]] = []
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and inp[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))
            comps.append(cells)
    return comps


def _go_left(cells: List[Tuple[int, int]]) -> bool:
    obj = set(cells)
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    top_gap = sum(1 for c in range(c0, c1 + 1) if (r0, c) not in obj)
    bot_gap = sum(1 for c in range(c0, c1 + 1) if (r1, c) not in obj)
    left_gap = sum(1 for r in range(r0, r1 + 1) if (r, c0) not in obj)
    right_gap = sum(1 for r in range(r0, r1 + 1) if (r, c1) not in obj)
    border: List[Tuple[int, int]] = []
    for c in range(c0, c1 + 1):
        border.append((r0, c))
        border.append((r1, c))
    for r in range(r0, r1 + 1):
        border.append((r, c0))
        border.append((r, c1))
    reach: set = set()
    q: deque = deque()
    for p in border:
        if p not in obj:
            reach.add(p)
            q.append(p)
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if (
                r0 <= nr <= r1
                and c0 <= nc <= c1
                and (nr, nc) not in reach
                and (nr, nc) not in obj
            ):
                reach.add((nr, nc))
                q.append((nr, nc))
    enc = 0
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if (r, c) not in obj and (r, c) not in reach:
                enc += 1
    sealed = (top_gap + bot_gap + left_gap + right_gap) == 0
    return enc > 0 or sealed


def _apply(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    cnt = Counter(v for row in inp for v in row)
    if len(cnt) != 2:
        return None
    bg, ink = [c for c, _ in cnt.most_common(2)]
    comps = _components(inp, ink)
    if not comps:
        return None
    out = [[bg] * w for _ in range(h)]
    changed = False
    for cells in comps:
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        c0, c1 = min(cs), max(cs)
        go_left = _go_left(cells)
        col = 2 if go_left else 3
        dc = -c0 if go_left else (w - 1 - c1)
        for r, c in cells:
            nc = c + dc
            if not (0 <= nc < w):
                return None
            out[r][nc] = col
            changed = True
    return out if changed else None


def make_ink_sealed_open_side_dock() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _apply(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("ink_sealed_open_side_dock", make_ink_sealed_open_side_dock())]


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
            "engine": "s2_ink_sealed_open_side_dock",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_ink_sealed_open_side_dock",
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
