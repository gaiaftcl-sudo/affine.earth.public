"""S1 quad-band priority merge (FoT).

Grammar (zoom_in_crop):
  Split the canvas into four equal-height bands; merge cellwise by a learned
  color priority (lowest rank wins among nonzero band values).

Canonical close: AGI-2 test task 3d31c5b3.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _learn_priority(train: Sequence[Dict[str, Any]]) -> Optional[List[int]]:
    beats = set()
    colors = set()
    for example in train:
        gi, go = example["input"], example["output"]
        if len(gi) % 4 != 0:
            return None
        bh = len(gi) // 4
        if len(go) != bh or (go and len(go[0]) != len(gi[0])):
            return None
        bands = [gi[i * bh : (i + 1) * bh] for i in range(4)]
        for r in range(bh):
            for c in range(len(gi[0])):
                vals = [bands[i][r][c] for i in range(4) if bands[i][r][c] != 0]
                win = go[r][c]
                if win == 0 or win not in vals:
                    if win == 0 and not vals:
                        continue
                    if win == 0:
                        return None
                    continue
                for v in vals:
                    colors.add(v)
                    if v != win:
                        beats.add((win, v))
    if not colors:
        return None
    succ: Dict[int, set] = defaultdict(set)
    indeg = {c: 0 for c in colors}
    for a, b in beats:
        if b not in succ[a]:
            succ[a].add(b)
            indeg[b] += 1
    q = deque([c for c in colors if indeg[c] == 0])
    order: List[int] = []
    while q:
        x = q.popleft()
        order.append(x)
        for y in succ[x]:
            indeg[y] -= 1
            if indeg[y] == 0:
                q.append(y)
    if len(order) != len(colors):
        return None
    return order


def make_merge(priority: Sequence[int]) -> Transform:
    rank = {c: i for i, c in enumerate(priority)}

    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0] or len(inp) % 4 != 0:
            return None
        bh = len(inp) // 4
        bands = [inp[i * bh : (i + 1) * bh] for i in range(4)]
        w = len(inp[0])
        out = [[0] * w for _ in range(bh)]
        for r in range(bh):
            for c in range(w):
                vals = [bands[i][r][c] for i in range(4) if bands[i][r][c] != 0]
                if not vals:
                    continue
                out[r][c] = min(vals, key=lambda v: rank.get(v, 99))
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    prio = _learn_priority(train)
    if prio is None:
        return []
    return [("quad_band_priority_merge", make_merge(prio))]


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
            "engine": "s1_quad_band_priority_merge",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_quad_band_priority_merge",
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
