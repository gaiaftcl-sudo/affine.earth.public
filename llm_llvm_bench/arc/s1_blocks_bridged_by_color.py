"""S1 2×2 blocks bridged by a path color (FoT).

Grammar (zoom_in_crop → 1×1): find all solid 2×2 blocks of color `block`;
emit `yes` if they are linked by a 4-connected path of color `bridge`
(or touch orthogonally); else emit `no`.

Canonical close: AGI-2 test task 239be575 (block=2, bridge=8, yes=8, no=0).
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _find_2x2(inp: Grid, block: int) -> List[Tuple[int, int]]:
    h, w = len(inp), len(inp[0])
    out: List[Tuple[int, int]] = []
    for r in range(h - 1):
        for c in range(w - 1):
            if all(inp[r + dr][c + dc] == block for dr in (0, 1) for dc in (0, 1)):
                out.append((r, c))
    return out


def _blocks_bridged(inp: Grid, block: int, bridge: int) -> bool:
    blocks = _find_2x2(inp, block)
    if len(blocks) < 2:
        return False
    h, w = len(inp), len(inp[0])

    def cells(b: Tuple[int, int]) -> List[Tuple[int, int]]:
        r, c = b
        return [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]

    # Orthogonal touch between any two blocks
    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            for a in cells(blocks[i]):
                for b in cells(blocks[j]):
                    if abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1:
                        return True

    starts = set()
    goals = set()
    for i, b in enumerate(blocks):
        for r, c in cells(b):
            for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and inp[nr][nc] == bridge:
                    (starts if i == 0 else goals).add((nr, nc))
    # multi-block: BFS from block0 bridge-neighbors; goal = bridge-neighbors of any other
    goals = set()
    for i, b in enumerate(blocks):
        if i == 0:
            continue
        for r, c in cells(b):
            for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and inp[nr][nc] == bridge:
                    goals.add((nr, nc))
    q = deque(starts)
    seen = set(starts)
    while q:
        r, c = q.popleft()
        if (r, c) in goals:
            return True
        for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and inp[nr][nc] == bridge:
                seen.add((nr, nc))
                q.append((nr, nc))
    return False


def _learn(train: Sequence[Dict[str, Any]]) -> Optional[Tuple[int, int, int, int]]:
    for block in range(1, 10):
        for bridge in range(1, 10):
            if bridge == block:
                continue
            for yes in range(10):
                for no in range(10):
                    if yes == no:
                        continue

                    def xf(
                        inp: Grid,
                        block=block,
                        bridge=bridge,
                        yes=yes,
                        no=no,
                    ) -> Grid:
                        return [[yes if _blocks_bridged(inp, block, bridge) else no]]

                    if all(xf(ex["input"]) == ex["output"] for ex in train):
                        return block, bridge, yes, no
    return None


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    params = _learn(train)
    if params is None:
        return []
    block, bridge, yes, no = params

    def _xf(grid: Grid) -> Optional[Grid]:
        if not grid or not grid[0]:
            return None
        return [[yes if _blocks_bridged(grid, block, bridge) else no]]

    return [(f"blocks{block}_bridge{bridge}_yes{yes}_no{no}", _xf)]


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
            "engine": "s1_blocks_bridged_by_color",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_blocks_bridged_by_color",
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
