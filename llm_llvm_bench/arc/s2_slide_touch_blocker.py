"""S2 slide object until it touches blocker (FoT).

Grammar (same_canvas_rewrite):
  Exactly one color-2 component and one color-8 component.
  Translate the 2-object by the minimal Manhattan shift so it
  orthogonally touches the 8-object without overlap.

Canonical close: AGI-2 test task 05f2a901.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _components(grid: Grid, color: int) -> List[List[Tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps: List[List[Tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or seen[r][c]:
                continue
            cells: List[Tuple[int, int]] = []
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < h and 0 <= ny < w and not seen[nx][ny] and grid[nx][ny] == color:
                        seen[nx][ny] = True
                        q.append((nx, ny))
            comps.append(cells)
    return comps


def slide_touch_blocker(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    twos = _components(inp, 2)
    eights = _components(inp, 8)
    if len(twos) != 1 or len(eights) != 1:
        return None
    mover, blocker = twos[0], eights[0]
    bset = set(blocker)

    def touches(cells: List[Tuple[int, int]]) -> bool:
        for r, c in cells:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (r + dx, c + dy) in bset:
                    return True
        return False

    best: Optional[Tuple[int, int, int, List[Tuple[int, int]]]] = None
    for dr in range(-(h - 1), h):
        for dc in range(-(w - 1), w):
            moved = [(r + dr, c + dc) for r, c in mover]
            if any(r < 0 or c < 0 or r >= h or c >= w for r, c in moved):
                continue
            if set(moved) & bset:
                continue
            if not touches(moved):
                continue
            dist = abs(dr) + abs(dc)
            if best is None or dist < best[0] or (
                dist == best[0] and (abs(dr), abs(dc)) < (abs(best[1]), abs(best[2]))
            ):
                best = (dist, dr, dc, moved)
    if best is None:
        return None
    out: Grid = [[0] * w for _ in range(h)]
    for r, c in blocker:
        out[r][c] = 8
    for r, c in best[3]:
        out[r][c] = 2
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("slide_touch_blocker", slide_touch_blocker)]


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
            "engine": "s2_slide_touch_blocker",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_slide_touch_blocker",
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
    "slide_touch_blocker",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
