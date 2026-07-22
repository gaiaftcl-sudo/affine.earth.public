"""S2 eight-wall channel fill with no-8 corridor bridge (FoT).

Grammar (same_canvas_rewrite):
  Palette is {0, 8, X} for a single non-zero non-8 color X. Iteratively fill
  every 0 inside a horizontal or vertical run bounded by color-8 walls when
  that run already contains X (one-sided bounds count: a wall on either end).
  After channel saturation, any column with no 8s that carries X on at least
  two rows fills the closed interval between the extremal X rows (corridor
  bridge between dual frames). Licensed only on perfect train replay.

Canonical close: AGI-2 test task 3ad05f52.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_eight_channel_fill() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        vals = {c for row in inp for c in row}
        if 8 not in vals:
            return None
        others = sorted(v for v in vals if v not in (0, 8))
        if len(others) != 1:
            return None
        X = others[0]
        g = [row[:] for row in inp]

        def h_segs(r: int) -> List[Tuple[int, int]]:
            segs: List[Tuple[int, int]] = []
            c = 0
            while c < w:
                while c < w and g[r][c] == 8:
                    c += 1
                if c >= w:
                    break
                c0 = c
                while c < w and g[r][c] != 8:
                    c += 1
                segs.append((c0, c))
            return segs

        def v_segs(c: int) -> List[Tuple[int, int]]:
            segs: List[Tuple[int, int]] = []
            r = 0
            while r < h:
                while r < h and g[r][c] == 8:
                    r += 1
                if r >= h:
                    break
                r0 = r
                while r < h and g[r][c] != 8:
                    r += 1
                segs.append((r0, r))
            return segs

        changed = True
        guard = 0
        while changed and guard < 500:
            changed = False
            guard += 1
            for r in range(h):
                for c0, c1 in h_segs(r):
                    if X not in (g[r][c] for c in range(c0, c1)):
                        continue
                    if not (c0 > 0 or c1 < w):
                        continue
                    for c in range(c0, c1):
                        if g[r][c] == 0:
                            g[r][c] = X
                            changed = True
            for c in range(w):
                for r0, r1 in v_segs(c):
                    if X not in (g[r][c] for r in range(r0, r1)):
                        continue
                    if not (r0 > 0 or r1 < h):
                        continue
                    for r in range(r0, r1):
                        if g[r][c] == 0:
                            g[r][c] = X
                            changed = True

        for c in range(w):
            if any(g[r][c] == 8 for r in range(h)):
                continue
            xs = [r for r in range(h) if g[r][c] == X]
            if len(xs) < 2:
                continue
            for r in range(min(xs), max(xs) + 1):
                if g[r][c] == 0:
                    g[r][c] = X
        return g

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("eight_channel_fill", make_eight_channel_fill())]


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
            "engine": "s2_eight_channel_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_eight_channel_fill",
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
