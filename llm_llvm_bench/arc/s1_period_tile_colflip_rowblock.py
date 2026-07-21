"""S1 period-tile with column-flip on odd row-blocks (FoT).

Grammar: zoom_out_expand where output is scale×scale tiling of the input
motif, and odd row-blocks use a horizontal flip of the motif.

Canonical close: AGI-2 test task 00576224 (2×2 → 6×6, scale=3).
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


def period_tile_colflip_rowblock(inp: Grid, scale: int) -> Grid:
    ih, iw = len(inp), len(inp[0])
    oh, ow = ih * scale, iw * scale
    out: Grid = [[0] * ow for _ in range(oh)]
    for r in range(oh):
        br = r // ih
        ir = r % ih
        for c in range(ow):
            ic = c % iw
            if br % 2:
                out[r][c] = inp[ir][iw - 1 - ic]
            else:
                out[r][c] = inp[ir][ic]
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    scale = _infer_scale(train)
    if scale is None:
        return []

    def _xf(grid: Grid) -> Optional[Grid]:
        if not grid or not grid[0]:
            return None
        return period_tile_colflip_rowblock(grid, scale)

    return [(f"period{scale}_colflip_rowblock", _xf)]


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
            "engine": "s1_period_tile_colflip_rowblock",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_period_tile_colflip_rowblock",
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
    "period_tile_colflip_rowblock",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
