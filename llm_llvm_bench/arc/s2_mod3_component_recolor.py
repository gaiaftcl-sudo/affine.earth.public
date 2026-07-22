"""S2 mod-3 component recolor (FoT).

Grammar (same_canvas_rewrite):
  Enumerate 4-connected components of palette {1, 8} in reading order.
  Every component whose index ≡ 0 (mod 3) is recolored to 2.

Canonical close: AGI-2 test task 22a4bbc2.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _components(inp: Grid, colors: Sequence[int]) -> List[List[Tuple[int, int]]]:
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    comps: List[List[Tuple[int, int]]] = []
    color_set = set(colors)
    for r in range(h):
        for c in range(w):
            if inp[r][c] not in color_set or seen[r][c]:
                continue
            col = inp[r][c]
            q = deque([(r, c)])
            seen[r][c] = True
            cells: List[Tuple[int, int]] = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    r2, c2 = rr + dr, cc + dc
                    if (
                        0 <= r2 < h
                        and 0 <= c2 < w
                        and not seen[r2][c2]
                        and inp[r2][c2] == col
                    ):
                        seen[r2][c2] = True
                        q.append((r2, c2))
            comps.append(cells)
    return comps


def make_mod3_component_recolor(
    colors: Tuple[int, int] = (1, 8), paint: int = 2, mod: int = 3, rem: int = 0
) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        out = [list(row) for row in inp]
        comps = _components(inp, colors)
        if not comps:
            return None
        hit = False
        for j, cells in enumerate(comps):
            if j % mod == rem:
                hit = True
                for r, c in cells:
                    out[r][c] = paint
        return out if hit else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("mod3_component_recolor", make_mod3_component_recolor())]


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
            "engine": "s2_mod3_component_recolor",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_mod3_component_recolor",
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
