"""General 8-marker symmetry readout for ARC grids (twin-S indexing).

Color 8 paints an axis-aligned marker bbox on an N×N grid. Candidate readouts
map each marker cell (r, c) through S = N+1 (31 when N=30):

  BOTH: (S-r, S-c)
  LR:   (r, S-c)
  UD:   (S-r, c)
  MAIN: (c, r)
  ANTI: (S-c, S-r)

A mode survives only when every mapped cell is in-bounds and contains no 8s.
Preference: BOTH > LR > UD > MAIN > ANTI. Train-replay must license before
any test attempt is emitted. Canonical implementation also lives in
`marker8_twin31.py` (orchestrator LOCAL_HYBRID_SOLVER path).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
MODE_ORDER = ("BOTH", "LR", "UD", "MAIN", "ANTI")


def _bbox_color(grid: Grid, color: int = 8) -> Tuple[int, int, int, int]:
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
    if not cells:
        raise ValueError(f"no cells with marker color {color}")
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), max(rows), min(cols), max(cols)


def _map_cell(mode: str, r: int, c: int, n: int) -> Tuple[int, int]:
    s = n + 1
    if mode == "BOTH":
        return s - r, s - c
    if mode == "LR":
        return r, s - c
    if mode == "UD":
        return s - r, c
    if mode == "MAIN":
        return c, r
    if mode == "ANTI":
        return s - c, s - r
    raise ValueError(f"unknown mode {mode}")


def readout_mode(
    grid: Grid, mode: str, marker_color: int = 8
) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    n = len(grid)
    if any(len(row) != n for row in grid):
        return None
    try:
        r0, r1, c0, c1 = _bbox_color(grid, marker_color)
    except ValueError:
        return None
    out: Grid = []
    for r in range(r0, r1 + 1):
        row_out: List[int] = []
        for c in range(c0, c1 + 1):
            rr, cc = _map_cell(mode, r, c, n)
            if rr < 0 or cc < 0 or rr >= n or cc >= n:
                return None
            val = grid[rr][cc]
            if val == marker_color:
                return None
            row_out.append(val)
        out.append(row_out)
    return out


def surviving_modes(grid: Grid, marker_color: int = 8) -> List[str]:
    return [mode for mode in MODE_ORDER if readout_mode(grid, mode, marker_color) is not None]


def choose_mode(grid: Grid, marker_color: int = 8) -> Optional[str]:
    for mode in MODE_ORDER:
        if readout_mode(grid, mode, marker_color) is not None:
            return mode
    return None


def apply(grid: Grid, marker_color: int = 8) -> Optional[Grid]:
    mode = choose_mode(grid, marker_color)
    if mode is None:
        return None
    return readout_mode(grid, mode, marker_color)


def train_replay(
    train: Sequence[Dict[str, Any]], marker_color: int = 8
) -> Dict[str, Any]:
    pairs = []
    passes = 0
    for index, example in enumerate(train):
        grid = example["input"]
        expected = example["output"]
        mode = choose_mode(grid, marker_color)
        predicted = readout_mode(grid, mode, marker_color) if mode else None
        ok = predicted == expected
        passes += int(ok)
        pairs.append(
            {
                "train_index": index,
                "pass": ok,
                "chosen_mode": mode,
                "survivors": surviving_modes(grid, marker_color),
            }
        )
    total = len(train)
    return {
        "engine": "eight_marker_symmetry_readout",
        "marker_color": marker_color,
        "train_replay_pass": passes,
        "train_replay_total": total,
        "train_replay": f"{passes}/{total}",
        "ok": passes == total and total > 0,
        "perfect": passes == total and total > 0,
        "pairs": pairs,
        "mode_order": list(MODE_ORDER),
    }


def predictions_for_task(
    task: Dict[str, Any], marker_color: int = 8
) -> Tuple[Optional[List[Dict[str, Grid]]], Dict[str, Any]]:
    replay = train_replay(task["train"], marker_color)
    if not replay["ok"]:
        return None, replay
    attempts: List[Dict[str, Grid]] = []
    test_meta = []
    for index, case in enumerate(task["test"]):
        mode = choose_mode(case["input"], marker_color)
        grid = readout_mode(case["input"], mode, marker_color) if mode else None
        if grid is None:
            replay = dict(replay)
            replay["ok"] = False
            replay["perfect"] = False
            replay["test_error"] = f"no surviving mode for test[{index}]"
            return None, replay
        attempts.append(
            {"attempt_1": grid, "attempt_2": [list(row) for row in grid]}
        )
        test_meta.append(
            {
                "test_index": index,
                "chosen_mode": mode,
                "survivors": surviving_modes(case["input"], marker_color),
            }
        )
    replay = dict(replay)
    replay["tests"] = test_meta
    return attempts, replay
