"""S2 marker Chebyshev seat match (FoT).

Grammar (same_canvas_rewrite):
  5-cells are immovable blocks. Every other nonzero cell is a marker.
  Candidate seats are cells Chebyshev-adjacent to any 5. Assign markers to
  distinct seats by greedy min-cost matching with cost
  (cheb + 2*axis_penalty, ortho_penalty, manhattan), where axis_penalty is 0
  when the seat shares a row/col with the marker and ortho_penalty is 0 when
  the seat is orthogonally adjacent to a 5.

Canonical close: AGI-2 test task 1b8318e3.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _blocks5(inp: Grid) -> List[frozenset]:
    h, w = len(inp), len(inp[0])
    seen = set()
    out: List[frozenset] = []
    for r in range(h):
        for c in range(w):
            if inp[r][c] != 5 or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and inp[nr][nc] == 5
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            out.append(frozenset(cells))
    return out


def _all_seats(bbs: List[frozenset], h: int, w: int) -> List[Tuple[int, int, bool]]:
    if not bbs:
        return []
    five = set().union(*bbs)
    seen = set()
    seats: List[Tuple[int, int, bool]] = []
    for r, c in five:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and (rr, cc) not in five and (rr, cc) not in seen:
                    seen.add((rr, cc))
                    ortho = any(abs(rr - fr) + abs(cc - fc) == 1 for fr, fc in five)
                    seats.append((rr, cc, ortho))
    return seats


def _cost(r: int, c: int, rr: int, cc: int, ortho: bool) -> Tuple[int, int, int]:
    axis = 0 if (rr == r or cc == c) else 1
    cheb = max(abs(rr - r), abs(cc - c))
    ortho_pen = 0 if ortho else 1
    man = abs(rr - r) + abs(cc - c)
    return (cheb + 2 * axis, ortho_pen, man)


def make_marker_cheb_seat_match(bg: int = 0, block: int = 5) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        bbs = _blocks5(inp)
        if not bbs:
            return None
        markers = [
            (r, c, inp[r][c])
            for r in range(h)
            for c in range(w)
            if inp[r][c] not in (bg, block)
        ]
        if not markers:
            return None
        seats = _all_seats(bbs, h, w)
        if not seats:
            return None
        edges = []
        for i, (r, c, _col) in enumerate(markers):
            for j, (rr, cc, ortho) in enumerate(seats):
                edges.append((_cost(r, c, rr, cc, ortho), i, j))
        edges.sort()
        used_m: set = set()
        used_s: set = set()
        assign: Dict[int, int] = {}
        for _sc, i, j in edges:
            if i in used_m or j in used_s:
                continue
            used_m.add(i)
            used_s.add(j)
            assign[i] = j
        out = [[block if inp[r][c] == block else bg for c in range(w)] for r in range(h)]
        changed = False
        for i, (r, c, col) in enumerate(markers):
            if i in assign:
                rr, cc, _ = seats[assign[i]]
                out[rr][cc] = col
                if (rr, cc) != (r, c):
                    changed = True
            else:
                out[r][c] = col
        return out if changed else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("marker_cheb_seat_match", make_marker_cheb_seat_match())]


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
            "engine": "s2_marker_cheb_seat_match",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, _ = exact[0]
    passed = len(train)
    return {
        "engine": "s2_marker_cheb_seat_match",
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
