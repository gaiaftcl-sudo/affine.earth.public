"""S2 stamp motif to singleton-5 (FoT).

Grammar (same_canvas_rewrite):
  Among 4-connected non-background blobs, find exactly one singleton cell of
  color 5 (anchor) and exactly one multi-cell motif that contains a single 5.
  Translate the motif so its 5 lands on the anchor; paint non-5 motif colors
  into the destination and clear the anchor 5 (do not paint 5).

Canonical close: AGI-2 test task 2c737e39.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _blobs(inp: Grid, bg: int = 0) -> List[List[Tuple[int, int]]]:
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    out: List[List[Tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if inp[r][c] == bg or seen[r][c]:
                continue
            q = deque([(r, c)])
            seen[r][c] = True
            cells: List[Tuple[int, int]] = []
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and not seen[nx][ny]
                        and inp[nx][ny] != bg
                    ):
                        seen[nx][ny] = True
                        q.append((nx, ny))
            out.append(cells)
    return out


def make_stamp_motif_to_singleton5() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        bg = 0
        blobs = _blobs(inp, bg)
        singles = [
            b[0]
            for b in blobs
            if len(b) == 1 and inp[b[0][0]][b[0][1]] == 5
        ]
        motifs = [
            b
            for b in blobs
            if len(b) > 1 and sum(1 for r, c in b if inp[r][c] == 5) == 1
        ]
        if len(singles) != 1 or len(motifs) != 1:
            return None
        ar, ac = singles[0]
        motif = motifs[0]
        m5 = [(r, c) for r, c in motif if inp[r][c] == 5]
        sr, sc = m5[0]
        dr, dc = ar - sr, ac - sc
        out = [list(row) for row in inp]
        out[ar][ac] = bg
        for r, c in motif:
            col = inp[r][c]
            if col == 5:
                continue
            rr, cc = r + dr, c + dc
            if not (0 <= rr < h and 0 <= cc < w):
                return None
            out[rr][cc] = col
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("stamp_motif_to_singleton5", make_stamp_motif_to_singleton5())]


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
            "engine": "s2_stamp_motif_to_singleton5",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_stamp_motif_to_singleton5",
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
