"""S1 ones-block tally (FoT).

Grammar (zoom_in_crop):
  Count 4-connected components of color 1 with area exactly 4 (2×2 blocks).
  Emit a 1×W row of that many 1s left-aligned (W learned from train, usually 5).

Canonical close: AGI-2 test task 1fad071e.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _count_blocks(inp: Grid, color: int = 1, area: int = 4) -> int:
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    n = 0
    for r in range(h):
        for c in range(w):
            if inp[r][c] != color or seen[r][c]:
                continue
            q = deque([(r, c)])
            seen[r][c] = True
            cells = 0
            while q:
                x, y = q.popleft()
                cells += 1
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and not seen[nx][ny]
                        and inp[nx][ny] == color
                    ):
                        seen[nx][ny] = True
                        q.append((nx, ny))
            if cells == area:
                n += 1
    return n


def _learn(train: Sequence[Dict[str, Any]]) -> Optional[Tuple[int, int]]:
    widths = Counter()
    for example in train:
        go = example["output"]
        if len(go) != 1:
            return None
        widths[len(go[0])] += 1
        n = _count_blocks(example["input"])
        row = go[0]
        if row[:n] != [1] * n or any(x != 0 for x in row[n:]):
            return None
    if len(widths) != 1:
        return None
    return 1, widths.most_common(1)[0][0]


def make_tally(fill: int, width: int) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        n = _count_blocks(inp)
        if n > width:
            return None
        return [[fill] * n + [0] * (width - n)]

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    learned = _learn(train)
    if learned is None:
        return []
    fill, width = learned
    return [("ones_block_tally", make_tally(fill, width))]


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
            "engine": "s1_ones_block_tally",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_ones_block_tally",
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
    "solve_task",
    "submission_fragment",
    "train_replay",
]
