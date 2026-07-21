"""S1 panel odd-one-out language game (FoT).

Grammar family owned here:
  panel_odd_one_out (canonical: eval task 38007db0)
    S1: output width shrinks to one lattice panel (pitch+1).
    S2: border color forms a full-column lattice with constant pitch.
    S3: overlapping panels share border columns; per-cell vote across panels.
    S4: if exactly one value appears once among panel votes, emit that anomaly;
        otherwise emit the majority value.
    C4: exact panel grid; licensed only when every training pair replays.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _lattice_pitch(grid: Grid) -> Optional[int]:
    height, width = len(grid), len(grid[0])
    border = grid[0][0]
    for col in range(1, width):
        if all(grid[row][col] == border for row in range(height)):
            return col
    return None


def panel_odd_one_out(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    pitch = _lattice_pitch(grid)
    if pitch is None or pitch < 1:
        return None
    height, width = len(grid), len(grid[0])
    if (width - 1) % pitch != 0:
        return None
    panel_w = pitch + 1
    n_panels = (width - 1) // pitch
    if n_panels < 2:
        return None
    panels = [
        [row[i * pitch : i * pitch + panel_w] for row in grid] for i in range(n_panels)
    ]
    if any(len(panel[0]) != panel_w for panel in panels):
        return None
    out: Grid = []
    for row in range(height):
        out_row: List[int] = []
        for col in range(panel_w):
            values = [panels[i][row][col] for i in range(n_panels)]
            counts = Counter(values)
            uniques = [value for value, count in counts.items() if count == 1]
            if len(uniques) == 1 and len(counts) > 1:
                out_row.append(uniques[0])
            else:
                out_row.append(counts.most_common(1)[0][0])
        out.append(out_row)
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("panel_odd_one_out", panel_odd_one_out)]


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
            "engine": "s1_panel_odd_one_out",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_panel_odd_one_out",
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
        attempts.append(
            {"attempt_1": pred, "attempt_2": [list(row) for row in pred]}
        )
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
    "panel_odd_one_out",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
