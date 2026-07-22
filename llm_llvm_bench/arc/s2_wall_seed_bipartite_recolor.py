"""S2 wall/seed bipartite recolor (FoT).

Grammar (same_canvas_rewrite):
  Wall color (7) is partitioned into 4-connected components. Seed color (2)
  components induce an adjacency graph on wall components (two wall comps are
  adjacent when both touch the same seed component). Bipartite-color that
  graph with palette (3, 5). Flip the two colors when the canvas has an even
  height or even width.

Canonical close: AGI-2 test task 3bd292e8.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _components(inp: Grid, color: int) -> List[List[Tuple[int, int]]]:
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    comps: List[List[Tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if inp[r][c] != color or seen[r][c]:
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
                        and inp[r2][c2] == color
                    ):
                        seen[r2][c2] = True
                        q.append((r2, c2))
            comps.append(cells)
    return comps


def make_wall_seed_bipartite_recolor(
    wall: int = 7, seed: int = 2, a: int = 3, b: int = 5
) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        comps = _components(inp, wall)
        if not comps:
            return None
        seed_comps = _components(inp, seed)
        cell2comp = {rc: i for i, cells in enumerate(comps) for rc in cells}
        adj: Dict[int, set] = {i: set() for i in range(len(comps))}
        for scells in seed_comps:
            touch = set()
            for r, c in scells:
                for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    key = (r + dr, c + dc)
                    if key in cell2comp:
                        touch.add(cell2comp[key])
            touch_l = list(touch)
            for i in range(len(touch_l)):
                for j in range(i + 1, len(touch_l)):
                    adj[touch_l[i]].add(touch_l[j])
                    adj[touch_l[j]].add(touch_l[i])
        color: List[Optional[int]] = [None] * len(comps)
        for i in range(len(comps)):
            if color[i] is not None:
                continue
            q = deque([i])
            color[i] = 0
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if color[v] is None:
                        color[v] = 1 - int(color[u])
                        q.append(v)
        flip = (h % 2 == 0) or (w % 2 == 0)
        out = [list(row) for row in inp]
        for i, cells in enumerate(comps):
            col = 0 if color[i] is None else int(color[i])
            if flip:
                col = 1 - col
            val = a if col == 0 else b
            for r, c in cells:
                out[r][c] = val
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("wall_seed_bipartite_recolor", make_wall_seed_bipartite_recolor())]


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
            "engine": "s2_wall_seed_bipartite_recolor",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_wall_seed_bipartite_recolor",
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
