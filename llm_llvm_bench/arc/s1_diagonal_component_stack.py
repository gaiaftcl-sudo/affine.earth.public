"""S1 diagonal component stack (FoT).

Grammar (zoom_in_crop / rearrange):
  Extract same-color 4-connected components, sort left-to-right by min column.
  Place each component's tight shape onto a blank canvas starting at (0,0),
  advancing the cursor by (height-1, width-1) after each (diagonal staircase).

Canonical close: AGI-2 test task 03560426.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_stack() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        seen = [[False] * w for _ in range(h)]
        comps: List[Tuple[int, int, List[Tuple[int, int]]]] = []
        for r in range(h):
            for c in range(w):
                if inp[r][c] == 0 or seen[r][c]:
                    continue
                col = inp[r][c]
                cells: List[Tuple[int, int]] = []
                q = deque([(r, c)])
                seen[r][c] = True
                while q:
                    x, y = q.popleft()
                    cells.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if (
                            0 <= nx < h
                            and 0 <= ny < w
                            and not seen[nx][ny]
                            and inp[nx][ny] == col
                        ):
                            seen[nx][ny] = True
                            q.append((nx, ny))
                comps.append((min(cc for _, cc in cells), col, cells))
        if not comps:
            return None
        comps.sort()
        out = [[0] * w for _ in range(h)]
        r_off = c_off = 0
        for _, col, cells in comps:
            rs = [rr for rr, _ in cells]
            cs = [cc for _, cc in cells]
            r0, c0 = min(rs), min(cs)
            bh, bw = max(rs) - r0 + 1, max(cs) - c0 + 1
            for rr, cc in cells:
                nr, nc = r_off + (rr - r0), c_off + (cc - c0)
                if 0 <= nr < h and 0 <= nc < w:
                    out[nr][nc] = col
            r_off += bh - 1
            c_off += bw - 1
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("diagonal_component_stack", make_stack())]


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
            "engine": "s1_diagonal_component_stack",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_diagonal_component_stack",
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
