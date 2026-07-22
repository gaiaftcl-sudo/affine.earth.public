"""S2 dual-sprite presence XOR crop (FoT).

Grammar (zoom_in_crop):
  Exactly two nonzero 4-connected components (sprites). Align each to its
  top-left bbox origin as a binary presence mask, pad to a common canvas,
  XOR the masks (8 where they differ, 0 where equal), then crop to the
  nonzero bounding box. Licensed only on perfect train replay.

Canonical close: AGI-2 test task 2037f2c7.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _comps(grid: Grid) -> List[List[Tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    out: List[List[Tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or grid[r][c] == 0:
                continue
            cells: List[Tuple[int, int]] = []
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and grid[nr][nc] != 0
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))
            out.append(cells)
    return out


def _presence_mask(cells: Sequence[Tuple[int, int]]) -> Grid:
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    h, w = max(rs) - r0 + 1, max(cs) - c0 + 1
    m = [[0] * w for _ in range(h)]
    for r, c in cells:
        m[r - r0][c - c0] = 1
    return m


def _pad(m: Grid, h: int, w: int) -> Grid:
    return [row + [0] * (w - len(row)) for row in m] + [[0] * w] * (h - len(m))


def _crop_nonzero(g: Grid) -> Optional[Grid]:
    h, w = len(g), len(g[0])
    rs = [r for r in range(h) for c in range(w) if g[r][c]]
    cs = [c for r in range(h) for c in range(w) if g[r][c]]
    if not rs:
        return None
    return [g[r][min(cs) : max(cs) + 1] for r in range(min(rs), max(rs) + 1)]


def _apply(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    comps = _comps(inp)
    if len(comps) != 2:
        return None
    ma, mb = _presence_mask(comps[0]), _presence_mask(comps[1])
    h = max(len(ma), len(mb))
    w = max(len(ma[0]), len(mb[0]))
    ma, mb = _pad(ma, h, w), _pad(mb, h, w)
    xor = [[8 if ma[r][c] != mb[r][c] else 0 for c in range(w)] for r in range(h)]
    return _crop_nonzero(xor)


def make_dual_sprite_presence_xor() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _apply(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("dual_sprite_presence_xor", make_dual_sprite_presence_xor())]


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
            "engine": "s2_dual_sprite_presence_xor",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_dual_sprite_presence_xor",
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
