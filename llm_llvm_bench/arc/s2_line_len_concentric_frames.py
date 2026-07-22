"""S2 line-length concentric frames (FoT).

Grammar (zoom_in_crop):
  Each nonzero straight line (horizontal or vertical component) contributes
  (color, length). Sort lengths descending; canvas size N = max length. Draw
  hollow square frames at inset 0,1,2,... in that order (inner 1x1 / 2x2 fill
  naturally). Licensed only on perfect train replay.

Canonical close: AGI-2 test task 3ee1011a.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_N4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _line_lengths(grid: Grid) -> Dict[int, int]:
    """Map length -> color for axis-aligned nonzero components."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    by_len: Dict[int, int] = {}
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or seen[r][c]:
                continue
            col = grid[r][c]
            q = deque([(r, c)])
            seen[r][c] = True
            cells: List[Tuple[int, int]] = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in _N4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and grid[nr][nc] == col
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))
            rs = {x for x, _ in cells}
            cs = {y for _, y in cells}
            if len(rs) == 1 or len(cs) == 1:
                by_len[len(cells)] = col
    return by_len


def make_line_len_concentric_frames() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        by_len = _line_lengths(inp)
        if not by_len:
            return None
        lengths = sorted(by_len.keys(), reverse=True)
        n = lengths[0]
        if n < 1:
            return None
        out = [[0] * n for _ in range(n)]
        for inset, ln in enumerate(lengths):
            col = by_len[ln]
            lo, hi = inset, n - 1 - inset
            if lo > hi:
                continue
            if lo == hi:
                out[lo][lo] = col
                continue
            for c in range(lo, hi + 1):
                out[lo][c] = col
                out[hi][c] = col
            for r in range(lo, hi + 1):
                out[r][lo] = col
                out[r][hi] = col
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("line_len_concentric_frames", make_line_len_concentric_frames())]


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
            "engine": "s2_line_len_concentric_frames",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_line_len_concentric_frames",
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
