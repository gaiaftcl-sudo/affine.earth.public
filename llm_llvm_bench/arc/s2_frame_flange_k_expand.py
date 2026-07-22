"""S2 frame flange expand by inner size k (FoT).

Grammar (same_canvas_rewrite):
  Non-bg object is a rectangular frame (outer color) enclosing an inner color
  block of size k×k. Recolor the original frame to the inner color and swap
  inner cells to the outer color. Then attach thickness-k orthogonal flanges
  of outer color on all four sides (corner k×k blocks stay background).

Canonical close: AGI-2 test task 3befdf3e.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_frame_flange_k_expand(bg: int = 0) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        cells = [(r, c) for r in range(h) for c in range(w) if inp[r][c] != bg]
        if not cells:
            return None
        vals = Counter(inp[r][c] for r, c in cells)
        if len(vals) < 2:
            return None
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        peri = [
            inp[r][c]
            for r, c in cells
            if r in (r0, r1) or c in (c0, c1)
        ]
        outer = Counter(peri).most_common(1)[0][0]
        others = [v for v in vals if v != outer]
        if len(others) != 1:
            return None
        inn = others[0]
        icells = [(r, c) for r, c in cells if inp[r][c] == inn]
        if not icells:
            return None
        ir0 = min(r for r, _ in icells)
        ir1 = max(r for r, _ in icells)
        ic0 = min(c for _, c in icells)
        ic1 = max(c for _, c in icells)
        kh, kw = ir1 - ir0 + 1, ic1 - ic0 + 1
        if kh != kw:
            return None
        k = kh
        out = [[bg] * w for _ in range(h)]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    out[r][c] = inn
                elif inp[r][c] == inn:
                    out[r][c] = outer
                elif inp[r][c] == outer:
                    out[r][c] = inn
        for i in range(1, k + 1):
            rr = r0 - i
            if rr >= 0:
                for c in range(c0, c1 + 1):
                    out[rr][c] = outer
            rr = r1 + i
            if rr < h:
                for c in range(c0, c1 + 1):
                    out[rr][c] = outer
            cc = c0 - i
            if cc >= 0:
                for r in range(r0, r1 + 1):
                    out[r][cc] = outer
            cc = c1 + i
            if cc < w:
                for r in range(r0, r1 + 1):
                    out[r][cc] = outer
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("frame_flange_k_expand", make_frame_flange_k_expand())]


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
            "engine": "s2_frame_flange_k_expand",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_frame_flange_k_expand",
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
