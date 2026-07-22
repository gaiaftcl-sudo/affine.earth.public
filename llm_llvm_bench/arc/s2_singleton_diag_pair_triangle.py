"""S2 singleton diagonal + pair triangle expand (FoT).

Grammar (same_canvas_rewrite):
  Freq-1 cells form one axis-aligned singleton line. Each empty cell takes the
  nearest main-diagonal and/or anti-diagonal singleton claim; when both hit,
  anti wins on the low side of the line and main on the high side. One-sided
  claims on the restricted flank are limited to the first band=2 seeds.
  Freq-2 adjacent pairs then expand: perpendicular pairs fill a gap-centered
  triangle toward the singleton line; parallel pairs either shear-expand by
  (gap - length) or, for horizontal overlays, expand toward the nearer end
  by (gap - 1) plus one inward diagonal from each pair seed.
  Licensed only on perfect train replay.

Canonical close: AGI-2 test task 1190bc91.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_BAND = 2


def _apply(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    freq = Counter(v for row in inp for v in row if v)
    if not freq or any(f not in (1, 2) for f in freq.values()):
        return None

    singles = [
        (r, c, inp[r][c])
        for r in range(h)
        for c in range(w)
        if freq[inp[r][c]] == 1
    ]
    if not singles:
        return None

    rs = {r for r, _, _ in singles}
    cs = {c for _, c, _ in singles}
    out = [row[:] for row in inp]

    if len(rs) == 1:
        s_orient = "h"
        s_r0 = next(iter(rs))
        s_a0, s_a1 = min(cs), max(cs)
        singles_sorted = sorted(singles, key=lambda x: x[1])
    elif len(cs) == 1:
        s_orient = "v"
        s_c0 = next(iter(cs))
        s_a0, s_a1 = min(rs), max(rs)
        singles_sorted = sorted(singles, key=lambda x: x[0])
    else:
        return None

    allowed = {(r, c) for r, c, _ in singles_sorted[:_BAND]}

    for r in range(h):
        for c in range(w):
            if inp[r][c]:
                continue
            main: List[Tuple[int, int, int, int]] = []
            anti: List[Tuple[int, int, int, int]] = []
            for sr, sc, col in singles:
                d = max(abs(r - sr), abs(c - sc))
                if (r - c) == (sr - sc):
                    main.append((d, col, sr, sc))
                if (r + c) == (sr + sc):
                    anti.append((d, col, sr, sc))
            main.sort()
            anti.sort()

            def best(
                lst: List[Tuple[int, int, int, int]], restricted: bool = False
            ) -> Optional[int]:
                if not lst:
                    return None
                if not restricted:
                    return lst[0][1]
                filt = [x for x in lst if (x[2], x[3]) in allowed]
                return filt[0][1] if filt else None

            color: Optional[int] = None
            if s_orient == "h":
                if main and anti:
                    color = best(anti) if r < s_r0 else best(main)
                elif main:
                    color = best(main)
                elif anti:
                    if r > s_r0:
                        color = best(anti, True)
                        if color is None:
                            color = 0
                    else:
                        color = best(anti)
            else:
                if main and anti:
                    color = best(anti) if c < s_c0 else best(main)
                elif anti:
                    color = best(anti)
                elif main:
                    if c < s_c0:
                        color = best(main, True)
                        if color is None:
                            color = 0
                    else:
                        color = best(main)
            if color is not None:
                out[r][c] = color

    def write(r: int, c: int, col: int) -> None:
        if 0 <= r < h and 0 <= c < w and inp[r][c] == 0:
            out[r][c] = col

    pairs = {
        col: [(r, c) for r in range(h) for c in range(w) if inp[r][c] == col]
        for col, f in freq.items()
        if f == 2
    }
    for col, cells in pairs.items():
        prs = sorted({r for r, _ in cells})
        pcs = sorted({c for _, c in cells})
        if len(prs) == 1:
            p_orient = "h"
            pr = prs[0]
            clo, chi = pcs[0], pcs[-1]
            plen = chi - clo + 1
        elif len(pcs) == 1:
            p_orient = "v"
            pc = pcs[0]
            rlo, rhi = prs[0], prs[-1]
            plen = rhi - rlo + 1
        else:
            continue

        if s_orient != p_orient:
            if s_orient == "h" and p_orient == "v":
                if pc < s_a0:
                    gap = s_a0 - pc
                    for c in range(pc, s_a0):
                        hw = gap - 1 - (c - pc)
                        if hw < 0:
                            continue
                        for r in range(s_r0 - hw, s_r0 + hw + 1):
                            write(r, c, col)
                elif pc > s_a1:
                    gap = pc - s_a1
                    for c in range(s_a1 + 1, pc + 1):
                        hw = gap - 1 - (pc - c)
                        if hw < 0:
                            continue
                        for r in range(s_r0 - hw, s_r0 + hw + 1):
                            write(r, c, col)
            else:
                if pr < s_a0:
                    gap = s_a0 - pr
                    for r in range(pr, s_a0):
                        hw = gap - 1 - (r - pr)
                        if hw < 0:
                            continue
                        for c in range(s_c0 - hw, s_c0 + hw + 1):
                            write(r, c, col)
                elif pr > s_a1:
                    gap = pr - s_a1
                    for r in range(s_a1 + 1, pr + 1):
                        hw = gap - 1 - (pr - r)
                        if hw < 0:
                            continue
                        for c in range(s_c0 - hw, s_c0 + hw + 1):
                            write(r, c, col)
        elif s_orient == "v":
            if pc > s_c0:
                gap = pc - s_c0
                for c in range(s_c0 + 1, pc + 1):
                    ext = gap - (pc - c) - plen
                    if ext < 0:
                        continue
                    for r in range(rlo - ext, rhi + ext + 1):
                        write(r, c, col)
            elif pc < s_c0:
                gap = s_c0 - pc
                for c in range(pc, s_c0):
                    ext = gap - (c - pc) - plen
                    if ext < 0:
                        continue
                    for r in range(rlo - ext, rhi + ext + 1):
                        write(r, c, col)
        else:
            if pr == s_r0:
                continue
            toward = 1 if pr < s_r0 else -1
            amt = abs(s_r0 - pr) - 1
            pair_center = (clo + chi) / 2
            seq_center = (s_a0 + s_a1) / 2
            if pair_center <= seq_center:
                for k in range(1, amt + 1):
                    write(pr, clo - k, col)
                for sr, sc in cells:
                    write(sr + toward, sc - 1, col)
            else:
                for k in range(1, amt + 1):
                    write(pr, chi + k, col)
                for sr, sc in cells:
                    write(sr + toward, sc + 1, col)

    return out


def make_singleton_diag_pair_triangle() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _apply(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("singleton_diag_pair_triangle", make_singleton_diag_pair_triangle())]


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
            "engine": "s2_singleton_diag_pair_triangle",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_singleton_diag_pair_triangle",
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
