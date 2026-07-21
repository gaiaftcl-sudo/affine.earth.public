"""S1 NW-wrap mark + period tile (FoT).

Grammar: zoom_out_expand where each nonzero cell stamps mark color at
wrapped (r-1, c-1), then the motif is period-tiled scale×scale.

Canonical close: AGI-2 test task 310f3251 (scale=3, mark=2).
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _infer_scale(train: Sequence[Dict[str, Any]]) -> Optional[int]:
    scales: List[int] = []
    for ex in train:
        inp, out = ex["input"], ex["output"]
        if not inp or not out or not inp[0] or not out[0]:
            return None
        ih, iw = len(inp), len(inp[0])
        oh, ow = len(out), len(out[0])
        if ih == 0 or iw == 0 or oh % ih or ow % iw:
            return None
        sh, sw = oh // ih, ow // iw
        if sh != sw or sh < 2:
            return None
        scales.append(sh)
    if not scales or len(set(scales)) != 1:
        return None
    return scales[0]


def nw_wrap_mark_period_tile(inp: Grid, scale: int, mark: int) -> Grid:
    h, w = len(inp), len(inp[0])
    motif = [list(row) for row in inp]
    for r in range(h):
        for c in range(w):
            if inp[r][c] == 0:
                continue
            nr, nc = (r - 1) % h, (c - 1) % w
            if motif[nr][nc] == 0:
                motif[nr][nc] = mark
    out: Grid = []
    for _ in range(scale):
        for row in motif:
            out.append(list(row) * scale)
    return out


def _learn_mark(train: Sequence[Dict[str, Any]], scale: int) -> Optional[int]:
    for mark in range(1, 10):
        if all(
            nw_wrap_mark_period_tile(ex["input"], scale, mark) == ex["output"]
            for ex in train
        ):
            return mark
    return None


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    scale = _infer_scale(train)
    if scale is None:
        return []
    mark = _learn_mark(train, scale)
    if mark is None:
        return []

    def _xf(grid: Grid) -> Optional[Grid]:
        if not grid or not grid[0]:
            return None
        return nw_wrap_mark_period_tile(grid, scale, mark)

    return [(f"nw_wrap_mark{mark}_period{scale}", _xf)]


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
            "engine": "s1_nw_wrap_mark_period_tile",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_nw_wrap_mark_period_tile",
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
    "exact_candidates",
    "named_candidates",
    "nw_wrap_mark_period_tile",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
