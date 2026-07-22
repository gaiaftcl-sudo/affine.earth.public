"""S2 wall marker extend (FoT).

Grammar (same_canvas_rewrite):
  Wall = a full row or full column of a single nonzero color (canonically 5).
  Non-wall nonzero runs are markers. Each marker extends toward the wall along
  its row (vertical wall) or column (horizontal wall), painting zeros only.
  Closest-to-wall markers are applied first so nearer fills win collisions.
  Licensed only on perfect train replay.

Canonical close: AGI-2 test task 13713586.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _find_wall(inp: Grid) -> Optional[Tuple[int, str, int]]:
    """Return (wall_color, 'row'|'col', wall_index) or None."""
    h, w = len(inp), len(inp[0])
    for cand in range(1, 10):
        rows = [r for r in range(h) if all(inp[r][c] == cand for c in range(w))]
        cols = [c for c in range(w) if all(inp[r][c] == cand for r in range(h))]
        if len(cols) == 1:
            return cand, "col", cols[0]
        if len(rows) == 1:
            return cand, "row", rows[0]
        # multi full-lines of same color: pick border-most
        if cols:
            if 0 in cols:
                return cand, "col", 0
            if (w - 1) in cols:
                return cand, "col", w - 1
            return cand, "col", cols[0]
        if rows:
            if 0 in rows:
                return cand, "row", 0
            if (h - 1) in rows:
                return cand, "row", h - 1
            return cand, "row", rows[0]
    return None


def _runs_1d(line: Sequence[int], wall_col: int) -> List[Tuple[int, int, int]]:
    """Return (start, end, color) runs of non-zero non-wall cells."""
    n = len(line)
    out: List[Tuple[int, int, int]] = []
    i = 0
    while i < n:
        v = line[i]
        if v not in (0, wall_col):
            j = i
            while j < n and line[j] == v:
                j += 1
            out.append((i, j - 1, v))
            i = j
        else:
            i += 1
    return out


def make_wall_marker_extend() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        wall = _find_wall(inp)
        if wall is None:
            return None
        wall_col, orient, widx = wall
        h, w = len(inp), len(inp[0])
        out = [row[:] for row in inp]
        if orient == "col":
            for r in range(h):
                sources = _runs_1d(inp[r], wall_col)
                sources.sort(key=lambda x: min(abs(x[0] - widx), abs(x[1] - widx)))
                for s, e, col in sources:
                    if e < widx:
                        for c in range(e + 1, widx):
                            if out[r][c] == 0:
                                out[r][c] = col
                    elif s > widx:
                        for c in range(widx + 1, s):
                            if out[r][c] == 0:
                                out[r][c] = col
        else:
            for c in range(w):
                line = [inp[r][c] for r in range(h)]
                sources = _runs_1d(line, wall_col)
                sources.sort(key=lambda x: min(abs(x[0] - widx), abs(x[1] - widx)))
                for s, e, col in sources:
                    if e < widx:
                        for r in range(e + 1, widx):
                            if out[r][c] == 0:
                                out[r][c] = col
                    elif s > widx:
                        for r in range(widx + 1, s):
                            if out[r][c] == 0:
                                out[r][c] = col
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("wall_marker_extend", make_wall_marker_extend())]


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
            "engine": "s2_wall_marker_extend",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_wall_marker_extend",
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
