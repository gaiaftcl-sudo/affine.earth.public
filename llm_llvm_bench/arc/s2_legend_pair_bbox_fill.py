"""S2 legend pair bbox fill (FoT).

Grammar (same_canvas_rewrite):
  Top-left 2-column key lists (source, fill) pairs until a zero breaks the
  column. Clear the key. For each pair in reverse key order, take the bbox of
  remaining source-colored markers, expand by 1, and paint empty cells with
  fill (later pairs overwrite earlier fills). Restore all non-key markers.
  Licensed only on perfect train replay.

Canonical close: AGI-2 test task 305b1341.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _parse_key(inp: Grid) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    pairs: List[Tuple[int, int]] = []
    cells: List[Tuple[int, int]] = []
    for r in range(len(inp)):
        if len(inp[r]) < 2:
            break
        a, b = inp[r][0], inp[r][1]
        if a == 0 or b == 0:
            break
        pairs.append((a, b))
        cells.extend([(r, 0), (r, 1)])
    return pairs, cells


def make_legend_pair_bbox_fill() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0] or len(inp[0]) < 2:
            return None
        h, w = len(inp), len(inp[0])
        pairs, key_cells = _parse_key(inp)
        if not pairs:
            return None
        g = [row[:] for row in inp]
        for r, c in key_cells:
            g[r][c] = 0
        out = [row[:] for row in g]
        for src, fill in reversed(pairs):
            cells = [(r, c) for r in range(h) for c in range(w) if g[r][c] == src]
            if not cells:
                continue
            rs = [r for r, _ in cells]
            cs = [c for _, c in cells]
            r0, r1 = max(0, min(rs) - 1), min(h - 1, max(rs) + 1)
            c0, c1 = max(0, min(cs) - 1), min(w - 1, max(cs) + 1)
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if g[r][c] == 0:
                        out[r][c] = fill
        for r in range(h):
            for c in range(w):
                if g[r][c] != 0:
                    out[r][c] = g[r][c]
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("legend_pair_bbox_fill", make_legend_pair_bbox_fill())]


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
            "engine": "s2_legend_pair_bbox_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_legend_pair_bbox_fill",
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
