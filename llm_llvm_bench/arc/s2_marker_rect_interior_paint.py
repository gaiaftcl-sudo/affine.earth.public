"""S2 marker-component maximal-rectangle interior paint (FoT).

Grammar (same_canvas_rewrite):
  Nonzero cells other than the field color 1 are markers. Each 4-connected
  component of (1 ∪ markers) that contains markers paints the interiors of
  every maximal solid axis-aligned rectangle inside that component with the
  component's marker color (train: one marker color per component).
  Interior: for h,w ≥ 3, strict bbox interior; for height-2 (width ≥ 3),
  drop left/right borders only; for width-2 (height ≥ 3), drop top/bottom
  only. Licensed only on perfect train replay.

Canonical close: AGI-2 test task 09c534e7.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_FIELD = 1


def _components(inp: Grid) -> List[Tuple[Set[Tuple[int, int]], List[Tuple[int, int, int]]]]:
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    out: List[Tuple[Set[Tuple[int, int]], List[Tuple[int, int, int]]]] = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or inp[r][c] == 0:
                continue
            cells: Set[Tuple[int, int]] = set()
            markers: List[Tuple[int, int, int]] = []
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                rr, cc = q.popleft()
                cells.add((rr, cc))
                v = inp[rr][cc]
                if v not in (0, _FIELD):
                    markers.append((rr, cc, v))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and inp[nr][nc] != 0:
                        seen[nr][nc] = True
                        q.append((nr, nc))
            out.append((cells, markers))
    return out


def _interior(r0: int, r1: int, c0: int, c1: int) -> Set[Tuple[int, int]]:
    hh = r1 - r0 + 1
    ww = c1 - c0 + 1
    cells: Set[Tuple[int, int]] = set()
    if hh >= 3 and ww >= 3:
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                cells.add((r, c))
    elif hh == 2 and ww >= 3:
        for r in range(r0, r1 + 1):
            for c in range(c0 + 1, c1):
                cells.add((r, c))
    elif ww == 2 and hh >= 3:
        for r in range(r0 + 1, r1):
            for c in range(c0, c1 + 1):
                cells.add((r, c))
    return cells


def _maximal_solid_rects(cells: Set[Tuple[int, int]]) -> List[Tuple[int, int, int, int]]:
    if len(cells) < 4:
        return []
    rmin = min(r for r, _ in cells)
    rmax = max(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    cmax = max(c for _, c in cells)
    candidates: List[Tuple[int, int, int, int]] = []
    for r0 in range(rmin, rmax + 1):
        active = {c for c in range(cmin, cmax + 1) if (r0, c) in cells}
        for r1 in range(r0, rmax + 1):
            if r1 > r0:
                active &= {c for c in range(cmin, cmax + 1) if (r1, c) in cells}
            if len(active) < 2:
                if not active:
                    break
                continue
            cols = sorted(active)
            i = 0
            while i < len(cols):
                j = i
                while j + 1 < len(cols) and cols[j + 1] == cols[j] + 1:
                    j += 1
                c0, c1 = cols[i], cols[j]
                if (r1 - r0 + 1) >= 2 and (c1 - c0 + 1) >= 2:
                    candidates.append((r0, r1, c0, c1))
                i = j + 1

    def expandable(r0: int, r1: int, c0: int, c1: int) -> bool:
        if r0 > rmin and all((r0 - 1, c) in cells for c in range(c0, c1 + 1)):
            return True
        if r1 < rmax and all((r1 + 1, c) in cells for c in range(c0, c1 + 1)):
            return True
        if c0 > cmin and all((r, c0 - 1) in cells for r in range(r0, r1 + 1)):
            return True
        if c1 < cmax and all((r, c1 + 1) in cells for r in range(r0, r1 + 1)):
            return True
        return False

    return [rect for rect in candidates if not expandable(*rect)]


def _apply(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    markers = [(r, c, inp[r][c]) for r in range(h) for c in range(w) if inp[r][c] not in (0, _FIELD)]
    if not markers:
        return None
    ones = sum(1 for row in inp for v in row if v == _FIELD)
    if ones < 8:
        return None

    out = [row[:] for row in inp]
    for cells, comps_markers in _components(inp):
        if not comps_markers:
            continue
        colors = {col for _, _, col in comps_markers}
        if len(colors) != 1:
            return None
        col = next(iter(colors))
        paint: Set[Tuple[int, int]] = set()
        for rect in _maximal_solid_rects(cells):
            paint |= _interior(*rect)
        for r, c in paint:
            if inp[r][c] == _FIELD:
                out[r][c] = col
    return out


def make_marker_rect_interior_paint() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _apply(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("marker_rect_interior_paint", make_marker_rect_interior_paint())]


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
            "engine": "s2_marker_rect_interior_paint",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_marker_rect_interior_paint",
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
