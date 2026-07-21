"""Marker-8 twin-31 readout for ARC tasks such as 0934a4d8.

Rule (FoT, train replay 4/4 on 0934a4d8):
  - Color 8 marks an axis-aligned bbox on an N×N grid (N=30 for 0934a4d8).
  - Each output cell is the twin of the corresponding marker-bbox cell.
  - Primary twin is rot180 through S=N+1: g[S-r][S-c] (0-indexed).
  - A candidate survives only when every twin is in-bounds and not color 8.
  - Mode order: BOTH > LR > UD > MAIN(transpose g[c][r]) > ANTI.
  - Prefer BOTH whenever it survives (perfect on all four 0934a4d8 train pairs).
  - OOB / marker twins fall through; test 0934a4d8 keeps MAIN only.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
MARKER = 8
ModeFn = Callable[[int, int], Tuple[int, int]]

MODE_ORDER = ("BOTH", "LR", "UD", "MAIN", "ANTI")


def grid_shape(grid: Grid) -> Tuple[int, int]:
    if not grid:
        return (0, 0)
    return (len(grid), len(grid[0]) if grid[0] else 0)


def marker_bbox(grid: Grid) -> Optional[Tuple[int, int, int, int]]:
    coords = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == MARKER
    ]
    if not coords:
        return None
    rows = [r for r, _ in coords]
    cols = [c for _, c in coords]
    return (min(rows), max(rows), min(cols), max(cols))


def _in_bounds(grid: Grid, r: int, c: int) -> bool:
    return 0 <= r < len(grid) and 0 <= c < len(grid[0])


def mode_fns(n: int) -> Dict[str, ModeFn]:
    """Index twins with S = N+1 (31 when N=30)."""
    s = n + 1
    return {
        "BOTH": lambda r, c: (s - r, s - c),
        "LR": lambda r, c: (r, s - c),
        "UD": lambda r, c: (s - r, c),
        "MAIN": lambda r, c: (c, r),
        "ANTI": lambda r, c: (s - c, s - r),
    }


def readout(grid: Grid, mode: str) -> Optional[Grid]:
    bbox = marker_bbox(grid)
    if bbox is None:
        return None
    n, _ = grid_shape(grid)
    fns = mode_fns(n)
    if mode not in fns:
        return None
    fn = fns[mode]
    r0, r1, c0, c1 = bbox
    out: Grid = []
    for r in range(r0, r1 + 1):
        row: List[int] = []
        for c in range(c0, c1 + 1):
            tr, tc = fn(r, c)
            if not _in_bounds(grid, tr, tc):
                return None
            value = grid[tr][tc]
            if value == MARKER:
                return None
            row.append(value)
        out.append(row)
    return out


def surviving_modes(grid: Grid) -> List[str]:
    return [mode for mode in MODE_ORDER if readout(grid, mode) is not None]


def choose_mode(grid: Grid) -> Optional[str]:
    survivors = surviving_modes(grid)
    return survivors[0] if survivors else None


def solve_grid(grid: Grid) -> Optional[Grid]:
    mode = choose_mode(grid)
    if mode is None:
        return None
    return readout(grid, mode)


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    pairs = []
    passed = 0
    for index, example in enumerate(task.get("train", [])):
        grid = example["input"]
        expected = example["output"]
        mode = choose_mode(grid)
        pred = readout(grid, mode) if mode else None
        ok = pred == expected
        passed += int(ok)
        bbox = marker_bbox(grid)
        pairs.append(
            {
                "train_index": index,
                "pass": ok,
                "chosen_mode": mode,
                "survivors": surviving_modes(grid),
                "marker_bbox": list(bbox) if bbox else None,
                "output_shape": list(grid_shape(pred)) if pred is not None else None,
            }
        )
    total = len(task.get("train", []))
    return {
        "engine": "marker8_twin31",
        "train_replay": f"{passed}/{total}",
        "perfect": total > 0 and passed == total,
        "passed": passed,
        "total": total,
        "pairs": pairs,
    }


def solve_task(task: Dict[str, Any]) -> Optional[List[Dict[str, Grid]]]:
    """Return attempt pairs only when every training pair replays exactly."""
    replay = train_replay(task)
    if not replay["perfect"]:
        return None
    attempts: List[Dict[str, Grid]] = []
    for case in task.get("test", []):
        pred = solve_grid(case["input"])
        if pred is None:
            return None
        attempts.append(
            {"attempt_1": pred, "attempt_2": [list(row) for row in pred]}
        )
    return attempts


def submission_fragment(task_id: str, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    attempts = solve_task(task)
    if attempts is None:
        return None
    return {task_id: attempts}


def describe_test(task: Dict[str, Any]) -> Dict[str, Any]:
    if not task.get("test"):
        return {}
    grid = task["test"][0]["input"]
    mode = choose_mode(grid)
    pred = readout(grid, mode) if mode else None
    bbox = marker_bbox(grid)
    return {
        "chosen_mode": mode,
        "survivors": surviving_modes(grid),
        "marker_bbox": list(bbox) if bbox else None,
        "output_shape": list(grid_shape(pred)) if pred is not None else None,
        "prediction": pred,
    }


def applies(task: Dict[str, Any]) -> bool:
    """True when marker-8 bbox twin-31 licenses every train pair."""
    return bool(train_replay(task)["perfect"])


__all__ = [
    "MARKER",
    "MODE_ORDER",
    "applies",
    "choose_mode",
    "describe_test",
    "marker_bbox",
    "mode_fns",
    "readout",
    "solve_grid",
    "solve_task",
    "submission_fragment",
    "surviving_modes",
    "train_replay",
]
