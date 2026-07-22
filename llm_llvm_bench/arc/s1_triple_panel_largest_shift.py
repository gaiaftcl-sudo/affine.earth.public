"""S1 triple-panel largest-component shift merge (FoT).

Grammar (zoom_in_crop):
  Input is three equal panels separated by all-zero divider columns.
  For each panel, take the largest 4-connected non-background (≠8) component.
  Stamp components left-to-right into a blank bg=8 canvas of panel size; when
  a component cannot land at its native offset (collision or OOB), shift it by
  the smallest Manhattan distance that fits (tie-break: smaller |dc|, |dr|,
  then left/up).

Canonical close: AGI-2 test task 337b420f (2 test grids).
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]


def _panels(inp: Grid) -> Optional[List[Grid]]:
    h, w = len(inp), len(inp[0])
    sep = [c for c in range(w) if all(inp[r][c] == 0 for r in range(h))]
    if not sep:
        return None
    bounds = [-1] + sep + [w]
    ps: List[Grid] = []
    for i in range(len(bounds) - 1):
        a, b = bounds[i] + 1, bounds[i + 1]
        if a < b:
            ps.append([row[a:b] for row in inp])
    if len(ps) != 3:
        return None
    ph, pw = len(ps[0]), len(ps[0][0])
    if ph == 0 or pw == 0:
        return None
    if any(len(p) != ph or len(p[0]) != pw for p in ps):
        return None
    return ps


def _largest_comp(panel: Grid, bg: int) -> Optional[Tuple[int, List[Cell]]]:
    h, w = len(panel), len(panel[0])
    seen = [[False] * w for _ in range(h)]
    comps: List[Tuple[int, List[Cell]]] = []
    for r in range(h):
        for c in range(w):
            if panel[r][c] == bg or seen[r][c]:
                continue
            col = panel[r][c]
            q = deque([(r, c)])
            seen[r][c] = True
            cells: List[Cell] = []
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and not seen[nx][ny]
                        and panel[nx][ny] == col
                    ):
                        seen[nx][ny] = True
                        q.append((nx, ny))
            comps.append((col, cells))
    if not comps:
        return None
    return max(comps, key=lambda item: len(item[1]))


def make_triple_panel_largest_shift(bg: int = 8) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        ps = _panels(inp)
        if ps is None:
            return None
        ph, pw = len(ps[0]), len(ps[0][0])
        out = [[bg] * pw for _ in range(ph)]
        for panel in ps:
            lc = _largest_comp(panel, bg)
            if lc is None:
                continue
            col, cells = lc

            def can_place(dr: int, dc: int) -> Optional[List[Cell]]:
                pos: List[Cell] = []
                for r, c in cells:
                    rr, cc = r + dr, c + dc
                    if not (0 <= rr < ph and 0 <= cc < pw):
                        return None
                    if out[rr][cc] != bg:
                        return None
                    pos.append((rr, cc))
                return pos

            placed: Optional[List[Cell]] = None
            for dist in range(0, ph + pw + 1):
                cands: List[Tuple[int, int, List[Cell]]] = []
                for dr in range(-dist, dist + 1):
                    for dc in range(-dist, dist + 1):
                        if abs(dr) + abs(dc) != dist:
                            continue
                        pos = can_place(dr, dc)
                        if pos is not None:
                            cands.append((dr, dc, pos))
                if cands:
                    cands.sort(
                        key=lambda x: (
                            abs(x[0]) + abs(x[1]),
                            abs(x[1]),
                            abs(x[0]),
                            x[1],
                            x[0],
                        )
                    )
                    placed = cands[0][2]
                    break
            if placed is None:
                return None
            for r, c in placed:
                out[r][c] = col
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("triple_panel_largest_shift", make_triple_panel_largest_shift())]


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
            "engine": "s1_triple_panel_largest_shift",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_triple_panel_largest_shift",
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
