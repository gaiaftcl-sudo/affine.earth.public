"""S2 open-rectangle bay pour (FoT).

Grammar (same_canvas_rewrite):
  Find near-rectangular frames of color 1. Missing perimeter cells are the
  bay opening(s). Fill interior background with 2, fill each opening cell,
  and pour 2 outward through background until blocked.

Canonical close: AGI-2 test task 292dd178.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_open_rect_bay_pour(frame: int = 1, fill: int = 2) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        bg = Counter(v for row in inp for v in row).most_common(1)[0][0]
        out = [list(row) for row in inp]
        seen = [[False] * w for _ in range(h)]
        found = False
        for r in range(h):
            for c in range(w):
                if inp[r][c] != frame or seen[r][c]:
                    continue
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
                            and inp[r2][c2] == frame
                        ):
                            seen[r2][c2] = True
                            q.append((r2, c2))
                if len(cells) < 6:
                    continue
                rs = [x for x, _ in cells]
                cs = [y for _, y in cells]
                r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
                perim = set()
                for cc in range(c0, c1 + 1):
                    perim.add((r0, cc))
                    perim.add((r1, cc))
                for rr in range(r0, r1 + 1):
                    perim.add((rr, c0))
                    perim.add((rr, c1))
                if sum(1 for rc in cells if rc in perim) < len(cells) * 0.8:
                    continue
                missing = perim - set(cells)
                if not missing:
                    continue
                found = True
                for rr in range(r0 + 1, r1):
                    for cc in range(c0 + 1, c1):
                        if out[rr][cc] == bg:
                            out[rr][cc] = fill
                for mr, mc in missing:
                    if mr == r0:
                        dr, dc = -1, 0
                    elif mr == r1:
                        dr, dc = 1, 0
                    elif mc == c0:
                        dr, dc = 0, -1
                    elif mc == c1:
                        dr, dc = 0, 1
                    else:
                        continue
                    if out[mr][mc] == bg:
                        out[mr][mc] = fill
                    rr, cc = mr, mc
                    while True:
                        rr += dr
                        cc += dc
                        if not (0 <= rr < h and 0 <= cc < w):
                            break
                        if out[rr][cc] != bg:
                            break
                        out[rr][cc] = fill
        return out if found else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("open_rect_bay_pour", make_open_rect_bay_pour())]


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
            "engine": "s2_open_rect_bay_pour",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_open_rect_bay_pour",
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
