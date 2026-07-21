"""S1 line color sequence (FoT).

Grammar (zoom_in_crop):
  Detect full/long horizontal, vertical, and diagonal lines (including a
  near-full zero row). Emit their colors as a 1×K row: if 0 is a line color,
  sorted unique colors; else interleave V/H by key (desc when ≥5 lines) and
  insert diagonals after the first VH pair.

Canonical close: AGI-2 test task 22425bda.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _classify(grid: Grid) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]], List[Tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    cnt = Counter(c for row in grid for c in row)
    vs: List[Tuple[int, int]] = []
    hs: List[Tuple[int, int]] = []
    ds: List[Tuple[int, int]] = []
    for color in cnt:
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        if len(cells) < 2:
            continue
        rs = {r for r, _ in cells}
        cs = {c for _, c in cells}
        if any(all(grid[r][c] == color for c in range(w)) for r in range(h)) or (
            len(rs) == 1 and len(cells) >= max(3, w // 2)
        ):
            key = next(
                r
                for r in range(h)
                if sum(1 for c in range(w) if grid[r][c] == color) >= max(3, w // 2)
            )
            hs.append((key, color))
        elif any(all(grid[r][c] == color for r in range(h)) for c in range(w)) or (
            len(cs) == 1 and len(cells) >= max(3, h // 2)
        ):
            vs.append((next(iter(cs)), color))
        elif len({r - c for r, c in cells}) == 1 and len(cells) >= max(3, min(h, w) // 2):
            ds.append((min(r - c for r, c in cells), color))
        elif len({r + c for r, c in cells}) == 1 and len(cells) >= max(3, min(h, w) // 2):
            ds.append((min(r + c for r, c in cells), color))
    return vs, hs, ds


def make_sequence() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        vs, hs, ds = _classify(inp)
        colors = {c for _, c in vs + hs + ds}
        if not colors:
            return None
        if 0 in colors:
            return [sorted(colors)]
        descending = len(vs) + len(hs) + len(ds) >= 5
        vs = sorted(vs, reverse=descending)
        hs = sorted(hs, reverse=descending)
        ds = sorted(ds, reverse=descending)
        out: List[int] = []
        i = j = 0
        dlist = list(ds)
        while i < len(vs) or j < len(hs):
            if i < len(vs):
                out.append(vs[i][1])
                i += 1
            if j < len(hs):
                out.append(hs[j][1])
                j += 1
            if i == 1 and j == 1 and dlist:
                out.extend(c for _, c in dlist)
                dlist = []
        out.extend(c for _, c in dlist)
        return [out]

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("line_color_sequence", make_sequence())]


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
            "engine": "s1_line_color_sequence",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_line_color_sequence",
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
