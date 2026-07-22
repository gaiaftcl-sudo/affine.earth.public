"""S1 dense-blob color grid (FoT).

Grammar (zoom_in_crop):
  Large near-rectangular same-color 4-connected components (high bbox fill)
  are the objects. Output shape is taken from the train demo whose object
  count matches the input. Objects are sorted by cy, partitioned into oh
  bands of ow, each band sorted by cx; each cell is that object's color.

Canonical close: AGI-2 test task 0a1d4ef5.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _large_rects(grid: Grid, min_n: int) -> List[Dict[str, Any]]:
    h0, w0 = len(grid), len(grid[0])
    seen = [[False] * w0 for _ in range(h0)]
    out: List[Dict[str, Any]] = []
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
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h0
                        and 0 <= ny < w0
                        and not seen[nx][ny]
                        and grid[nx][ny] == col
                    ):
                        seen[nx][ny] = True
                        q.append((nx, ny))
            if len(cells) < min_n:
                continue
            rs = [a for a, _ in cells]
            cs = [b for _, b in cells]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            area = (r1 - r0 + 1) * (c1 - c0 + 1)
            fill = len(cells) / area if area else 0.0
            out.append(
                {
                    "col": col,
                    "n": len(cells),
                    "fill": fill,
                    "cy": (r0 + r1) / 2.0,
                    "cx": (c0 + c1) / 2.0,
                }
            )
    return out


def _count_objs(grid: Grid, min_n: int = 12, thr: float = 0.75) -> List[Dict[str, Any]]:
    return [o for o in _large_rects(grid, min_n) if o["fill"] >= thr]


def _pick_objs(grid: Grid, need: int) -> Optional[List[Dict[str, Any]]]:
    for thr in (0.75, 0.7, 0.8, 0.65, 0.55, 0.9):
        for mn in (12, 10, 15, 8, 16, 20, 25):
            cand = _count_objs(grid, min_n=mn, thr=thr)
            if len(cand) == need:
                return cand
    return None


def make_dense_blob_color_grid(train: Sequence[Dict[str, Any]]) -> Transform:
    demos = list(train)

    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0] or not demos:
            return None
        objs = _count_objs(inp, min_n=12, thr=0.75)
        if len(objs) < 2:
            objs = _count_objs(inp, min_n=10, thr=0.7)
        best = None
        for ex in demos:
            co = _count_objs(ex["input"], min_n=12, thr=0.75)
            if len(co) == len(objs):
                best = ex
                break
        if best is None:
            best = min(
                demos,
                key=lambda ex: abs(
                    len(_count_objs(ex["input"], min_n=12, thr=0.75)) - len(objs)
                ),
            )
        oh, ow = len(best["output"]), len(best["output"][0])
        need = oh * ow
        if len(objs) != need:
            objs2 = _pick_objs(inp, need)
            if objs2 is None:
                return None
            objs = objs2
        objs = sorted(objs, key=lambda o: o["cy"])
        out: Grid = [[0] * ow for _ in range(oh)]
        for i in range(oh):
            band = objs[i * ow : (i + 1) * ow]
            band = sorted(band, key=lambda o: o["cx"])
            for j, o in enumerate(band):
                out[i][j] = int(o["col"])
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("dense_blob_color_grid", make_dense_blob_color_grid(train))]


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
            "engine": "s1_dense_blob_color_grid",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_dense_blob_color_grid",
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
