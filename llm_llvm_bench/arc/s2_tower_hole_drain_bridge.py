"""S2 tower-hole drain / bridge (FoT).

Grammar (same_canvas_rewrite):
  Holes (0) sit in wall color (2) on a bg field (7).
  - Multi-tower holes (≥2 holes stacked in wall columns): bridge the min hole
    row between outer hole columns, clear wall below each hole, and place a
    special adjacent wall cell beside the lower hole.
  - Otherwise per-hole: drain one contiguous wall run (prefer pure-bg side /
    right), then stack that mass into the hole column (prefer down if enough
    free bg, else up with leftover down).

Canonical close: AGI-2 test task 230f2e48.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_tower_hole_drain_bridge(
    wall: int = 2, hole: int = 0, bg: int = 7
) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        out = [list(row) for row in inp]
        holes = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == hole]

        def is_tower_hole(hr: int, hc: int) -> bool:
            return (hr > 0 and inp[hr - 1][hc] == wall) or (
                hr + 1 < h and inp[hr + 1][hc] == wall
            )

        if len(holes) >= 2 and all(is_tower_hole(r, c) for r, c in holes):
            r0 = min(r for r, _ in holes)
            cols = sorted(c for _, c in holes)
            for c in range(cols[0] + 1, cols[-1] - 1):
                if out[r0][c] == bg:
                    out[r0][c] = wall
            for r, c in holes:
                out[r][c] = hole
            for hr, hc in holes:
                for r in range(hr + 1, h):
                    if out[r][hc] == wall:
                        out[r][hc] = bg
                if hr > r0 and hc > 0 and out[hr][hc - 1] == bg:
                    out[hr][hc - 1] = wall
            return out

        for hr, hc in holes:
            left: List[int] = []
            c = hc - 1
            while c >= 0 and out[hr][c] == wall:
                left.append(c)
                c -= 1
            right: List[int] = []
            c = hc + 1
            while c < w and out[hr][c] == wall:
                right.append(c)
                c += 1

            def beyond(cells: List[int], side: str) -> Optional[int]:
                if not cells:
                    return None
                if side == "L":
                    cc = cells[-1] - 1
                    return out[hr][cc] if cc >= 0 else None
                cc = cells[-1] + 1
                return out[hr][cc] if cc < w else None

            cands: List[Tuple[str, List[int], Optional[int]]] = []
            if left:
                cands.append(("L", left, beyond(left, "L")))
            if right:
                cands.append(("R", right, beyond(right, "R")))
            if not cands:
                continue
            pure = [c for c in cands if c[2] in (bg, None)]
            if len(pure) == 1:
                cells = pure[0][1]
            elif len(pure) > 1:
                cells = next(
                    (c[1] for c in pure if c[0] == "R"),
                    pure[0][1],
                )
            else:
                cands.sort(key=lambda c: (-len(c[1]), 0 if c[0] == "R" else 1))
                cells = cands[0][1]
            for c in cells:
                out[hr][c] = bg
            n = len(cells)
            below = sum(1 for r in range(hr + 1, h) if out[r][hc] == bg)
            if below >= n:
                r = hr + 1
                while n > 0 and r < h:
                    if out[r][hc] == bg:
                        out[r][hc] = wall
                        n -= 1
                    r += 1
            else:
                r = hr - 1
                while n > 0 and r >= 0:
                    if out[r][hc] == bg:
                        out[r][hc] = wall
                        n -= 1
                    r -= 1
                r = hr + 1
                while n > 0 and r < h:
                    if out[r][hc] == bg:
                        out[r][hc] = wall
                        n -= 1
                    r += 1
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("tower_hole_drain_bridge", make_tower_hole_drain_bridge())]


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
            "engine": "s2_tower_hole_drain_bridge",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_tower_hole_drain_bridge",
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
