"""S2 polygon corner-4 / inset-2 (FoT).

Grammar (same_canvas_rewrite):
  Single non-zero color C. For each C cell with exactly two orthogonal C
  neighbors forming an L:
    - if the L's inner diagonal is also C → paint 2
    - else if that open diagonal is exterior background (0s flood-touching
      the canvas border) → paint 2
    - else (open diagonal is a hole) → paint 4

Canonical close: AGI-2 test task 15663ba9.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _exterior_zeros(inp: Grid) -> set:
    h, w = len(inp), len(inp[0])
    ext: set = set()
    q: deque = deque()
    for r in range(h):
        for c in (0, w - 1):
            if inp[r][c] == 0 and (r, c) not in ext:
                ext.add((r, c))
                q.append((r, c))
    for c in range(w):
        for r in (0, h - 1):
            if inp[r][c] == 0 and (r, c) not in ext:
                ext.add((r, c))
                q.append((r, c))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < h and 0 <= ny < w and inp[nx][ny] == 0 and (nx, ny) not in ext:
                ext.add((nx, ny))
                q.append((nx, ny))
    return ext


def make_poly_corner_4_inset_2() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        nonzero = [v for row in inp for v in row if v]
        if not nonzero:
            return None
        base = Counter(nonzero).most_common(1)[0][0]
        if any(v not in (0, base) for row in inp for v in row):
            return None
        S = {(r, c) for r in range(h) for c in range(w) if inp[r][c] == base}
        if not S:
            return None
        ext = _exterior_zeros(inp)
        out = [row[:] for row in inp]
        changed = False
        for r, c in S:
            up = (r - 1, c) in S
            down = (r + 1, c) in S
            left = (r, c - 1) in S
            right = (r, c + 1) in S
            if sum((up, down, left, right)) != 2:
                continue
            if not ((up or down) and (left or right)):
                continue
            dr = -1 if up else 1
            dc = -1 if left else 1
            diag = (r + dr, c + dc)
            if diag in S:
                out[r][c] = 2
            elif diag in ext:
                out[r][c] = 2
            else:
                out[r][c] = 4
            changed = True
        return out if changed else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("poly_corner_4_inset_2", make_poly_corner_4_inset_2())]


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
            "engine": "s2_poly_corner_4_inset_2",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_poly_corner_4_inset_2",
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
