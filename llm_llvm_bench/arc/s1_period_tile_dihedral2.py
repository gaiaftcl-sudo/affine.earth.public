"""S1 2×2 dihedral period-tile (FoT).

Grammar: zoom_out_expand where output is a 2×2 block assembly of the input
motif under the Klein dihedral corners (I, H, V, HV):

  [ I | H  ]
  [ V | HV ]

Canonical close: AGI-2 test task 3af2c5a8 (3×4 → 6×8).
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _hflip(grid: Grid) -> Grid:
    return [list(reversed(row)) for row in grid]


def _vflip(grid: Grid) -> Grid:
    return list(reversed([list(row) for row in grid]))


def period_tile_dihedral2(inp: Grid) -> Grid:
    i = [list(row) for row in inp]
    h = _hflip(i)
    v = _vflip(i)
    hv = _hflip(v)
    top = [a + b for a, b in zip(i, h)]
    bot = [a + b for a, b in zip(v, hv)]
    return top + bot


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    if not train:
        return []
    for ex in train:
        inp, out = ex["input"], ex["output"]
        if not inp or not out or not inp[0] or not out[0]:
            return []
        ih, iw = len(inp), len(inp[0])
        oh, ow = len(out), len(out[0])
        if oh != 2 * ih or ow != 2 * iw:
            return []

    def _xf(grid: Grid) -> Optional[Grid]:
        if not grid or not grid[0]:
            return None
        return period_tile_dihedral2(grid)

    return [("period2_dihedral_I_H_V_HV", _xf)]


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
            "engine": "s1_period_tile_dihedral2",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_period_tile_dihedral2",
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
    "period_tile_dihedral2",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
