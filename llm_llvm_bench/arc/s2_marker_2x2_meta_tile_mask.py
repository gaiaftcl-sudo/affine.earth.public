"""S2 marker 2x2 meta tile-mask recolor (FoT).

Grammar (same_canvas_rewrite):
  Wall lattice on period-4 (rows/cols with color 4). Marker color M is the sole
  color outside {0,1,4}. Pack non-overlapping solid 2x2 blocks of M; their
  relative block indices (÷2 from min TL) form a mask. In every 4x4 tile, if all
  mask cells are 1, recolor those cells to M. Licensed only on perfect train replay.

Canonical close: AGI-2 test task 15113be4.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _marker_color(grid: Grid) -> Optional[int]:
    colors = Counter(v for row in grid for v in row)
    mcols = [c for c in colors if c not in (0, 1, 4)]
    if len(mcols) != 1:
        return None
    return int(mcols[0])


def _packed_2x2_tls(grid: Grid, color: int) -> List[Tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    raw: List[Tuple[int, int]] = []
    for r in range(h - 1):
        for c in range(w - 1):
            if (
                grid[r][c] == color
                and grid[r][c + 1] == color
                and grid[r + 1][c] == color
                and grid[r + 1][c + 1] == color
            ):
                raw.append((r, c))
    raw.sort()
    taken: Set[Tuple[int, int]] = set()
    kept: List[Tuple[int, int]] = []
    for r, c in raw:
        cells = {(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)}
        if cells & taken:
            continue
        taken |= cells
        kept.append((r, c))
    return kept


def _meta_mask(tls: Sequence[Tuple[int, int]]) -> Optional[Set[Tuple[int, int]]]:
    if not tls:
        return None
    r0 = min(r for r, _ in tls)
    c0 = min(c for _, c in tls)
    if any((r - r0) % 2 or (c - c0) % 2 for r, c in tls):
        return None
    return {((r - r0) // 2, (c - c0) // 2) for r, c in tls}


def make_marker_2x2_meta_tile_mask() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        m = _marker_color(inp)
        if m is None:
            return None
        tls = _packed_2x2_tls(inp, m)
        mask = _meta_mask(tls)
        if not mask:
            return None
        out = [row[:] for row in inp]
        changed = False
        for i in range(0, h, 4):
            for j in range(0, w, 4):
                pos: List[Tuple[int, int]] = []
                ok = True
                for dr, dc in mask:
                    r, c = i + dr, j + dc
                    if not (0 <= r < h and 0 <= c < w) or inp[r][c] != 1:
                        ok = False
                        break
                    pos.append((r, c))
                if not ok:
                    continue
                for r, c in pos:
                    if out[r][c] != m:
                        changed = True
                    out[r][c] = m
        return out if changed else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("marker_2x2_meta_tile_mask", make_marker_2x2_meta_tile_mask())]


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
            "engine": "s2_marker_2x2_meta_tile_mask",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_marker_2x2_meta_tile_mask",
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
