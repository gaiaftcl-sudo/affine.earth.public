"""S2 magnet-to-full-line (FoT).

Grammar (same_canvas_rewrite):
  Detect full-row or full-column solid lines. Keep those lines. Other cells of
  a line's color move to the adjacent row/col touching the nearest same-color
  line; colors without a line are deleted.

Canonical close: AGI-2 test task 1a07d186.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_magnet_to_full_line() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        out = [[0] * w for _ in range(h)]
        hlines: List[Tuple[int, int]] = []
        vlines: List[Tuple[int, int]] = []
        for r in range(h):
            if all(inp[r][c] != 0 for c in range(w)) and len(set(inp[r])) == 1:
                hlines.append((r, inp[r][0]))
        for c in range(w):
            if all(inp[r][c] != 0 for r in range(h)) and len({inp[r][c] for r in range(h)}) == 1:
                vlines.append((c, inp[0][c]))
        hby: Dict[int, List[int]] = defaultdict(list)
        for r, col in hlines:
            hby[col].append(r)
        vby: Dict[int, List[int]] = defaultdict(list)
        for c, col in vlines:
            vby[col].append(c)
        for r, col in hlines:
            out[r] = [col] * w
        for c, col in vlines:
            for r in range(h):
                out[r][c] = col
        if hlines:
            for r in range(h):
                for c in range(w):
                    v = inp[r][c]
                    if v == 0:
                        continue
                    if any(r == lr and v == col for lr, col in hlines):
                        continue
                    if v not in hby:
                        continue
                    target = min(hby[v], key=lambda lr: abs(lr - r))
                    dest = target - 1 if r < target else target + 1
                    if 0 <= dest < h:
                        out[dest][c] = v
        elif vlines:
            for r in range(h):
                for c in range(w):
                    v = inp[r][c]
                    if v == 0:
                        continue
                    if any(c == lc and v == col for lc, col in vlines):
                        continue
                    if v not in vby:
                        continue
                    target = min(vby[v], key=lambda lc: abs(lc - c))
                    dest = target - 1 if c < target else target + 1
                    if 0 <= dest < w:
                        out[r][dest] = v
        else:
            return None
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("magnet_to_full_line", make_magnet_to_full_line())]


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
            "engine": "s2_magnet_to_full_line",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_magnet_to_full_line",
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
