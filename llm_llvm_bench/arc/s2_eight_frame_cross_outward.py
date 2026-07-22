"""S2 eight-frame cross outward fill (FoT).

Grammar (same_canvas_rewrite):
  Color-8 cells define a hollow rectangle by their bbox. Draw that frame in 8.
  Fill every zero in the cross-band (frame row-span OR col-span) from the frame
  with the unique non-8 color that appears inside the bbox (primary). Restore
  original non-8 seeds. Each seed in a cross arm floods only outward from the
  frame along its row (horizontal arms) or column (vertical arms), conquering
  primary cells. Corner regions outside the cross stay untouched.
  Licensed only on perfect train replay.

Canonical close: AGI-2 test task 256b0a75.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _apply(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    eights = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == 8]
    if len(eights) < 4:
        return None
    rs = [r for r, _ in eights]
    cs = [c for _, c in eights]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    if r1 - r0 < 2 or c1 - c0 < 2:
        return None
    inside = Counter(
        inp[r][c]
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if inp[r][c] not in (0, 8)
    )
    if not inside:
        return None
    primary = inside.most_common(1)[0][0]
    out = [row[:] for row in inp]
    for c in range(c0, c1 + 1):
        out[r0][c] = 8
        out[r1][c] = 8
    for r in range(r0, r1 + 1):
        out[r][c0] = 8
        out[r][c1] = 8

    def in_cross(r: int, c: int) -> bool:
        return (r0 <= r <= r1) or (c0 <= c <= c1)

    q: deque[Tuple[int, int]] = deque(
        (r, c) for r in range(h) for c in range(w) if out[r][c] == 8
    )
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and out[nr][nc] == 0 and in_cross(nr, nc):
                out[nr][nc] = primary
                q.append((nr, nc))

    seeds: List[Tuple[int, int, int]] = []
    for r in range(h):
        for c in range(w):
            if inp[r][c] not in (0, 8) and out[r][c] != 8:
                out[r][c] = inp[r][c]
                if in_cross(r, c):
                    seeds.append((r, c, inp[r][c]))

    for r, c, col in seeds:
        if r0 <= r <= r1 and c < c0:
            nc = c - 1
            while nc >= 0 and out[r][nc] == primary:
                out[r][nc] = col
                nc -= 1
        if r0 <= r <= r1 and c > c1:
            nc = c + 1
            while nc < w and out[r][nc] == primary:
                out[r][nc] = col
                nc += 1
        if c0 <= c <= c1 and r < r0:
            nr = r - 1
            while nr >= 0 and out[nr][c] == primary:
                out[nr][c] = col
                nr -= 1
        if c0 <= c <= c1 and r > r1:
            nr = r + 1
            while nr < h and out[nr][c] == primary:
                out[nr][c] = col
                nr += 1
    return out


def make_eight_frame_cross_outward() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _apply(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("eight_frame_cross_outward", make_eight_frame_cross_outward())]


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
            "engine": "s2_eight_frame_cross_outward",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_eight_frame_cross_outward",
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
