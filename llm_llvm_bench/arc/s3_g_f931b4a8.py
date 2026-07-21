"""Batch FoT engine for eval task f931b4a8.

Grammar family owned here:
  g_f931b4a8 (canonical: eval task f931b4a8)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · f931b4a8). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_f931b4a8(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


import json
import numpy as np

def solve(input_grid):
    grid = np.array(input_grid)
    H, W = grid.shape
    hh, hw = H // 2, W // 2
    
    TL = grid[:hh, :hw]
    TR = grid[:hh, hw:]
    BL = grid[hh:, :hw]
    BR = grid[hh:, hw:]
    
    # Count non-black cells
    tl_count = int(np.sum(TL != 0))
    tr_count = int(np.sum(TR != 0))
    
    # Determine pattern and fill
    br_nonblack = int(np.sum(BR != 0))
    
    if br_nonblack > 0:
        pattern = BR
        fill = BL
    else:
        pattern = BL
        fill = BR
    
    pH, pW = pattern.shape
    
    # Output dimensions
    out_rows = tl_count if tl_count > 0 else pH
    out_cols = tr_count if tr_count > 0 else pW
    
    # Build output
    output = np.zeros((out_rows, out_cols), dtype=int)
    for r in range(out_rows):
        for c in range(out_cols):
            pr = r % pH
            pc = c % pW
            if pattern[pr][pc] != 0:
                output[r][c] = pattern[pr][pc]
            else:
                tr = r // pH
                tc = c // pW
                fr = tr % fill.shape[0]
                fc = tc % fill.shape[1]
                output[r][c] = fill[fr][fc]
    
    return output.tolist()

# Test
EMOJI = ['⬛','🔴','🟢','💚','🟡','⬜','🟣','🟠','🔷','🟫']



def _solve(grid: Grid):
    return solve(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_f931b4a8", g_f931b4a8)]


def exact_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    out: List[Tuple[str, Transform]] = []
    for name, transform in named_candidates():
        if all(transform(ex["input"]) == ex["output"] for ex in train):
            out.append((name, transform))
    return out


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    train = task.get("train", [])
    exact = exact_candidates(train)
    if not exact:
        return {
            "engine": "s3_g_f931b4a8",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
            "primary_transform": None,
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_g_f931b4a8",
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
    "g_f931b4a8",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
