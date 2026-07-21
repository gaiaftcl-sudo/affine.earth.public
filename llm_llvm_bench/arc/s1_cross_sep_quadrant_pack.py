"""S1 cross-separator quadrant pack (FoT).

Grammar (zoom_in_crop):
  A full uniform-color row and a full (or majority) uniform-color column
  of the same separator color split the canvas into 4 quadrants.
  Pack each quadrant's nonzero (non-sep) bbox into a 3×3 tile and
  assemble as a 6×6 (TL, TR, BL, BR).

Canonical close: AGI-2 test task 0bb8deee.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _stamp_quad(part: Grid, sep_color: int, size: int = 3) -> Grid:
    if not part or not part[0]:
        return [[0] * size for _ in range(size)]
    cells = [
        (r, c)
        for r in range(len(part))
        for c in range(len(part[0]))
        if part[r][c] != 0 and part[r][c] != sep_color
    ]
    out = [[0] * size for _ in range(size)]
    if not cells:
        return out
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    for r, c in cells:
        rr, cc = r - r0, c - c0
        if 0 <= rr < size and 0 <= cc < size:
            out[rr][cc] = part[r][c]
    return out


def cross_sep_quadrant_pack(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    sep_rows = [
        r
        for r in range(h)
        if 0 not in set(inp[r]) and len(set(inp[r])) == 1
    ]
    if not sep_rows:
        return None
    rsep = sep_rows[0]
    sep_color = inp[rsep][0]
    sep_cols = [c for c in range(w) if all(inp[r][c] == sep_color for r in range(h))]
    if not sep_cols:
        sep_cols = [
            c
            for c in range(w)
            if sum(1 for r in range(h) if inp[r][c] == sep_color) >= h // 2
        ]
    if not sep_cols:
        return None
    csep = sep_cols[0]
    quads = [
        [row[:csep] for row in inp[:rsep]],
        [row[csep + 1 :] for row in inp[:rsep]],
        [row[:csep] for row in inp[rsep + 1 :]],
        [row[csep + 1 :] for row in inp[rsep + 1 :]],
    ]
    tiles = [_stamp_quad(q, sep_color) for q in quads]
    out: Grid = [[0] * 6 for _ in range(6)]
    for (tr, tc), g in zip([(0, 0), (0, 3), (3, 0), (3, 3)], tiles):
        for r in range(3):
            for c in range(3):
                out[tr + r][tc + c] = g[r][c]
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("cross_sep_quadrant_pack", cross_sep_quadrant_pack)]


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
            "engine": "s1_cross_sep_quadrant_pack",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_cross_sep_quadrant_pack",
        "train_replay": f"{passed}/{len(train)}",
        "perfect": passed == len(train) and len(train) > 0,
        "passed": passed,
        "total": len(train),
        "licensed_transforms": [n for n, _ in exact],
        "primary_transform": name,
    }


def solve_task(task: Dict[str, Any]) -> Optional[List[Dict[str, Grid]]]:
    replay = train_replay(task)
    if not replay["perfect"]:
        return None
    exact = exact_candidates(task["train"])
    _, transform = exact[0]
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
    "cross_sep_quadrant_pack",
    "exact_candidates",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
