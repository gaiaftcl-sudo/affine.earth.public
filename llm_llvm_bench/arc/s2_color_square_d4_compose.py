"""S2 color square-embed D4 compose (FoT).

Grammar (zoom_in_crop):
  Background = mode color. For each other color, embed its bbox into a square
  of side max(h,w) (top-left aligned), close under D4 about the square center,
  and center the result on a canvas of side max pattern diameter. Paint
  smallest patterns first (no overwrite) so larger frames fill around them.
  Licensed only on perfect train replay.

Canonical close: AGI-2 test task 4290ef0e.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _d4_rel(rel: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
    uni = set(rel)

    def rot90(s: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        return {(c, -r) for r, c in s}

    def refl(s: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        return {(-r, c) for r, c in s}

    cur = set(rel)
    for _ in range(4):
        uni |= cur
        cur = rot90(cur)
    cur = refl(rel)
    for _ in range(4):
        uni |= cur
        cur = rot90(cur)
    return uni


def _expand_color(cells: Set[Tuple[int, int]]) -> Optional[Tuple[Set[Tuple[int, int]], int]]:
    if not cells:
        return None
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    bh, bw = r1 - r0 + 1, c1 - c0 + 1
    side = max(bh, bw)
    local = {(r - r0, c - c0) for r, c in cells}
    cr = cc = side - 1
    rel = {(2 * r - cr, 2 * c - cc) for r, c in local}
    uni: Set[Tuple[int, int]] = set()
    for rr, cc_ in _d4_rel(rel):
        if (rr + cr) % 2 or (cc_ + cc) % 2:
            continue
        uni.add(((rr + cr) // 2, (cc_ + cc) // 2))
    if not uni:
        return None
    urs = [r for r, _ in uni]
    ucs = [c for _, c in uni]
    ur0, uc0 = min(urs), min(ucs)
    uni2 = {(r - ur0, c - uc0) for r, c in uni}
    urs = [r for r, _ in uni2]
    ucs = [c for _, c in uni2]
    diam = max(max(urs) + 1, max(ucs) + 1)
    return uni2, diam


def make_color_square_d4_compose() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        bg = Counter(v for row in inp for v in row).most_common(1)[0][0]
        by_col: Dict[int, Set[Tuple[int, int]]] = {}
        for r in range(h):
            for c in range(w):
                if inp[r][c] != bg:
                    by_col.setdefault(inp[r][c], set()).add((r, c))
        if not by_col:
            return None
        expanded: Dict[int, Tuple[Set[Tuple[int, int]], int]] = {}
        for col, cells in by_col.items():
            got = _expand_color(cells)
            if got is None:
                return None
            expanded[col] = got
        n = max(d for _, d in expanded.values())
        out = [[bg] * n for _ in range(n)]
        for col in sorted(expanded.keys(), key=lambda c: (expanded[c][1], len(expanded[c][0]))):
            uni2, _diam = expanded[col]
            rs = [r for r, _ in uni2]
            cs = [c for _, c in uni2]
            h1, w1 = max(rs) + 1, max(cs) + 1
            off_r = (n - h1) // 2
            off_c = (n - w1) // 2
            for r, c in uni2:
                rr, cc = r + off_r, c + off_c
                if out[rr][cc] == bg:
                    out[rr][cc] = col
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("color_square_d4_compose", make_color_square_d4_compose())]


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
            "engine": "s2_color_square_d4_compose",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_color_square_d4_compose",
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
