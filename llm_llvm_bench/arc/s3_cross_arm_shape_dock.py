"""S3 cross-arm shape dock language game (FoT).

Grammar family owned here:
  cross_arm_shape_dock (canonical: eval task 2c181942)
    S1: same canvas; background = 8.
    S2: locate unique 4×4 four-arm cross (distinct arm colors).
    S3: remaining same-color cells form a shape per arm color.
    S4: rotate each shape so its connecting face matches the arm;
        dock outward from that arm (prefer longest matching face).
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 2c181942). Never submits to Kaggle.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_BG = 8


def cross_arm_shape_dock(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    if len(out) != len(grid) or len(out[0]) != len(grid[0]):
        return None
    return out


def _rot90(shape: List[List[int]], k: int) -> List[List[int]]:
    out = [row[:] for row in shape]
    for _ in range(k % 4):
        h, w = len(out), len(out[0])
        out = [[out[h - 1 - r][c] for r in range(h)] for c in range(w)]
    return out


def _solve(grid: Grid) -> Grid:
    height, width = len(grid), len(grid[0])
    cross_pos = None
    arms: Optional[Dict[str, int]] = None
    for r in range(height - 3):
        for c in range(width - 3):
            center = [grid[r + dr][c : c + 4] for dr in range(4)]
            if not (
                center[1][1] == _BG
                and center[1][2] == _BG
                and center[2][1] == _BG
                and center[2][2] == _BG
                and center[0][0] == _BG
                and center[0][3] == _BG
                and center[3][0] == _BG
                and center[3][3] == _BG
            ):
                continue
            top, bottom = center[0][1], center[3][1]
            left, right = center[1][0], center[1][3]
            if (
                top == center[0][2]
                and top != _BG
                and bottom == center[3][2]
                and bottom != _BG
                and left == center[2][0]
                and left != _BG
                and right == center[2][3]
                and right != _BG
                and len({top, bottom, left, right}) == 4
            ):
                cross_pos = (r, c)
                arms = {
                    "top": int(top),
                    "bottom": int(bottom),
                    "left": int(left),
                    "right": int(right),
                }
                break
        if cross_pos is not None:
            break
    if cross_pos is None or arms is None:
        raise ValueError("no cross")

    cr, cc = cross_pos
    cross_cells = {
        (cr + dr, cc + dc)
        for dr in range(4)
        for dc in range(4)
        if grid[cr + dr][cc + dc] != _BG
    }

    color_cells: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
    for r in range(height):
        for c in range(width):
            if grid[r][c] != _BG and (r, c) not in cross_cells:
                color_cells[int(grid[r][c])].append((r, c))

    out = [[_BG for _ in range(width)] for _ in range(height)]
    for r, c in cross_cells:
        out[r][c] = grid[r][c]

    arm_meta = {
        "top": {"arm_rows": (cr, cr), "arm_cols": (cc + 1, cc + 2)},
        "bottom": {"arm_rows": (cr + 3, cr + 3), "arm_cols": (cc + 1, cc + 2)},
        "left": {"arm_rows": (cr + 1, cr + 2), "arm_cols": (cc, cc)},
        "right": {"arm_rows": (cr + 1, cr + 2), "arm_cols": (cc + 3, cc + 3)},
    }

    for direction, arm_color in arms.items():
        cells = color_cells.get(arm_color)
        if not cells:
            continue
        min_r = min(r for r, _ in cells)
        max_r = max(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        max_c = max(c for _, c in cells)
        shape = [
            [0 for _ in range(max_c - min_c + 1)] for _ in range(max_r - min_r + 1)
        ]
        for r, c in cells:
            shape[r - min_r][c - min_c] = 1

        meta = arm_meta[direction]
        arm_r1, arm_r2 = meta["arm_rows"]
        arm_c1, arm_c2 = meta["arm_cols"]

        candidates: List[Tuple[int, int, List[List[int]], int]] = []
        for k in range(4):
            rot = _rot90(shape, k)
            rh, rw = len(rot), len(rot[0])
            if direction in ("left", "right"):
                arm_center = (arm_r1 + arm_r2) / 2.0
                ext_r_start = int(round(arm_center - (rh - 1) / 2.0))
                face = [rot[r][-1] for r in range(rh)] if direction == "left" else [
                    rot[r][0] for r in range(rh)
                ]
                expected = [0] * rh
                for ar in range(arm_r1, arm_r2 + 1):
                    idx = ar - ext_r_start
                    if 0 <= idx < rh:
                        expected[idx] = 1
                if face == expected:
                    candidates.append((len(face), k, rot, ext_r_start))
            else:
                arm_center = (arm_c1 + arm_c2) / 2.0
                ext_c_start = int(round(arm_center - (rw - 1) / 2.0))
                face = rot[-1][:] if direction == "top" else rot[0][:]
                expected = [0] * rw
                for ac in range(arm_c1, arm_c2 + 1):
                    idx = ac - ext_c_start
                    if 0 <= idx < rw:
                        expected[idx] = 1
                if face == expected:
                    candidates.append((len(face), k, rot, ext_c_start))

        if not candidates:
            continue
        candidates.sort(key=lambda x: -x[0])
        _, _k, rot, start = candidates[0]
        rh, rw = len(rot), len(rot[0])

        if direction in ("left", "right"):
            ext_r_start = start
            ext_c_start = arm_c1 - rw if direction == "left" else arm_c2 + 1
            for r in range(rh):
                for c in range(rw):
                    if rot[r][c]:
                        pr, pc = ext_r_start + r, ext_c_start + c
                        if 0 <= pr < height and 0 <= pc < width:
                            out[pr][pc] = arm_color
        else:
            ext_c_start = start
            ext_r_start = arm_r1 - rh if direction == "top" else arm_r2 + 1
            for r in range(rh):
                for c in range(rw):
                    if rot[r][c]:
                        pr, pc = ext_r_start + r, ext_c_start + c
                        if 0 <= pr < height and 0 <= pc < width:
                            out[pr][pc] = arm_color

    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("cross_arm_shape_dock", cross_arm_shape_dock)]


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
            "engine": "s3_cross_arm_shape_dock",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_cross_arm_shape_dock",
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
    "cross_arm_shape_dock",
    "exact_candidates",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
