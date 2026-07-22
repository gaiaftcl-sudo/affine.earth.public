"""S2 height-3 solid-rect middle checker punch (FoT).

Grammar (same_canvas_rewrite):
  Find every 4-connected solid rectangular component whose height is exactly 3.
  In the middle row of each such rectangle, zero cells at odd offsets from the
  left edge of the rectangle (checker punch). All other cells unchanged.

Canonical close: AGI-2 test task 3bdb4ada.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]


def make_rect3_middle_checker_punch(bg: Optional[int] = None) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        flat = [v for row in inp for v in row]
        bg0 = Counter(flat).most_common(1)[0][0] if bg is None else bg
        out = [list(row) for row in inp]
        seen = [[False] * w for _ in range(h)]
        hit = False
        for r in range(h):
            for c in range(w):
                col = inp[r][c]
                if col == bg0 or seen[r][c]:
                    continue
                q = deque([(r, c)])
                seen[r][c] = True
                cells: List[Cell] = []
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
                rs = [x for x, _ in cells]
                cs = [y for _, y in cells]
                r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
                if r1 - r0 + 1 != 3:
                    continue
                if len(cells) != (r1 - r0 + 1) * (c1 - c0 + 1):
                    continue
                mid = r0 + 1
                for cc in range(c0, c1 + 1):
                    if (cc - c0) % 2 == 1:
                        out[mid][cc] = bg0
                        hit = True
        return out if hit else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("rect3_middle_checker_punch", make_rect3_middle_checker_punch())]


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
            "engine": "s2_rect3_middle_checker_punch",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_rect3_middle_checker_punch",
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
