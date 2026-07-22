"""S1 quad 3x3 motif pack (FoT).

Grammar (zoom_in_crop):
  Find 8-connected same-color components whose bbox fits in 3x3.
  Take the four components (or the four largest), sort into two cy-bands
  then by cx, and place their 3x3 bbox crops into a 7x7 canvas at
  (0,0), (0,4), (4,0), (4,4) — leaving a one-cell cross of zeros.

Canonical close: AGI-2 test task 1990f7a8.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _comps8(grid: Grid) -> List[Dict[str, Any]]:
    h0, w0 = len(grid), len(grid[0])
    seen = [[False] * w0 for _ in range(h0)]
    out: List[Dict[str, Any]] = []
    nbrs = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
    for r in range(h0):
        for c in range(w0):
            if grid[r][c] == 0 or seen[r][c]:
                continue
            col = grid[r][c]
            cells: List[Tuple[int, int]] = []
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in nbrs:
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h0
                        and 0 <= ny < w0
                        and not seen[nx][ny]
                        and grid[nx][ny] == col
                    ):
                        seen[nx][ny] = True
                        q.append((nx, ny))
            rs = [a for a, _ in cells]
            cs = [b for _, b in cells]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            h, w = r1 - r0 + 1, c1 - c0 + 1
            if h > 3 or w > 3:
                continue
            bbox = [
                [grid[rr][cc] for cc in range(c0, c1 + 1)] for rr in range(r0, r1 + 1)
            ]
            out.append(
                {
                    "n": len(cells),
                    "cy": (r0 + r1) / 2.0,
                    "cx": (c0 + c1) / 2.0,
                    "h": h,
                    "w": w,
                    "bbox": bbox,
                }
            )
    return out


def _to_3x3(bbox: Grid) -> Optional[Grid]:
    h, w = len(bbox), len(bbox[0])
    if h == 3 and w == 3:
        return [row[:] for row in bbox]
    if h > 3 or w > 3:
        return None
    out = [[0] * 3 for _ in range(3)]
    ro, co = (3 - h) // 2, (3 - w) // 2
    for r in range(h):
        for c in range(w):
            out[ro + r][co + c] = bbox[r][c]
    return out


def make_quad_3x3_motif_pack() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        comps = _comps8(inp)
        if len(comps) < 4:
            return None
        if len(comps) > 4:
            comps = sorted(comps, key=lambda o: -o["n"])[:4]
        comps = sorted(comps, key=lambda o: o["cy"])
        top = sorted(comps[:2], key=lambda o: o["cx"])
        bot = sorted(comps[2:], key=lambda o: o["cx"])
        tiles: List[Grid] = []
        for comp in top + bot:
            tile = _to_3x3(comp["bbox"])
            if tile is None:
                return None
            tiles.append(tile)
        out = [[0] * 7 for _ in range(7)]
        for (pr, pc), tile in zip(((0, 0), (0, 4), (4, 0), (4, 4)), tiles):
            for r in range(3):
                for c in range(3):
                    out[pr + r][pc + c] = tile[r][c]
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("quad_3x3_motif_pack", make_quad_3x3_motif_pack())]


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
            "engine": "s1_quad_3x3_motif_pack",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_quad_3x3_motif_pack",
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
