"""S2 separator-7 panel accent repack (FoT).

Grammar (same_canvas_rewrite):
  Full-7 rows split the canvas into panels. Each panel keeps its color-8
  scaffold. Each panel's unique non-7/non-8 accent (count N) is reassigned
  to a panel whose 8-silhouette can pack N cells: for rightmost-8 column
  ri per row, choose R with sum_i max(0, R-ri) == N, then fill columns
  ri+1..R with the accent. Accents are assigned greedily by (-count, -color)
  to the feasible panel with minimal R (then lowest panel index).

Canonical close: AGI-2 test task 18447a8d.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _panels(g: Grid) -> List[Tuple[int, int]]:
    h, w = len(g), len(g[0])
    seps = {i for i in range(h) if all(g[i][c] == 7 for c in range(w))}
    bands: List[Tuple[int, int]] = []
    i = 0
    while i < h:
        if i in seps:
            i += 1
            continue
        j = i
        while j < h and j not in seps:
            j += 1
        bands.append((i, j - 1))
        i = j
    return bands


def _rightmost8(g: Grid, r0: int, r1: int) -> List[int]:
    w = len(g[0])
    out: List[int] = []
    for r in range(r0, r1 + 1):
        rm = -1
        for c in range(w):
            if g[r][c] == 8:
                rm = c
        out.append(rm)
    return out


def _min_R(r8: Sequence[int], n: int) -> Optional[int]:
    for r in range(0, 32):
        if sum(max(0, r - ri) for ri in r8) == n:
            return r
    return None


def make_sep7_panel_accent_repack() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        if not any(v == 7 for row in inp for v in row):
            return None
        if not any(v == 8 for row in inp for v in row):
            return None
        ps = _panels(inp)
        if len(ps) < 2:
            return None
        accents: List[Tuple[int, int, int]] = []
        for i, (r0, r1) in enumerate(ps):
            if not any(inp[r][c] == 8 for r in range(r0, r1 + 1) for c in range(w)):
                return None
            cnt = Counter(
                inp[r][c]
                for r in range(r0, r1 + 1)
                for c in range(w)
                if inp[r][c] not in (7, 8)
            )
            if len(cnt) != 1:
                return None
            col, n = cnt.most_common(1)[0]
            accents.append((n, col, i))
        accents.sort(key=lambda x: (-x[0], -x[1]))
        assigned: Dict[int, Tuple[int, int, int]] = {}
        used = set()
        for n, col, _src in accents:
            cands: List[Tuple[int, int]] = []
            for j, (r0, r1) in enumerate(ps):
                if j in used:
                    continue
                R = _min_R(_rightmost8(inp, r0, r1), n)
                if R is not None:
                    cands.append((R, j))
            if not cands:
                return None
            cands.sort()
            R, j = cands[0]
            assigned[j] = (col, n, R)
            used.add(j)
        if len(assigned) != len(ps):
            return None
        out = [[7] * w for _ in range(h)]
        for r in range(h):
            for c in range(w):
                if inp[r][c] == 8:
                    out[r][c] = 8
        for j, (r0, r1) in enumerate(ps):
            col, _n, R = assigned[j]
            r8 = _rightmost8(inp, r0, r1)
            for k, r in enumerate(range(r0, r1 + 1)):
                ri = r8[k]
                for c in range(ri + 1, R + 1):
                    if 0 <= c < w and out[r][c] == 7:
                        out[r][c] = col
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("sep7_panel_accent_repack", make_sep7_panel_accent_repack())]


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
            "engine": "s2_sep7_panel_accent_repack",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_sep7_panel_accent_repack",
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
