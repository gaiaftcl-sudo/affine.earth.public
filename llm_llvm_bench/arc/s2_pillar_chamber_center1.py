"""S2 pillar-chamber center-1 (FoT).

Grammar (same_canvas_rewrite):
  Color-2 cells form row bars and column pillars. Between consecutive
  bars/pillars (and canvas borders) sit chambers. In each chamber, the
  bounding box of color-1 cells is re-placed centered (integer mid)
  inside that chamber; 2s stay fixed.

Canonical close: AGI-2 test task 20981f0e.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_pillar_chamber_center1(
    pillar: int = 2, move: int = 1, bg: int = 0
) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        pcols = sorted({c for r in range(h) for c in range(w) if inp[r][c] == pillar})
        prows = sorted({r for r in range(h) for c in range(w) if inp[r][c] == pillar})
        if len(pcols) < 1 or len(prows) < 2:
            return None
        crow = [-1] + prows + [h]
        ccol = [-1] + pcols + [w]
        out = [[bg] * w for _ in range(h)]
        for r in range(h):
            for c in range(w):
                if inp[r][c] == pillar:
                    out[r][c] = pillar
        moved = False
        for i in range(len(crow) - 1):
            r0, r1 = crow[i], crow[i + 1]
            if r1 - r0 <= 1:
                continue
            for j in range(len(ccol) - 1):
                c0, c1 = ccol[j], ccol[j + 1]
                if c1 - c0 <= 1:
                    continue
                cells = [
                    (r, c)
                    for r in range(r0 + 1, r1)
                    for c in range(c0 + 1, c1)
                    if inp[r][c] == move
                ]
                if not cells:
                    continue
                rs = [r for r, _ in cells]
                cs = [c for _, c in cells]
                rr0, rr1 = min(rs), max(rs)
                cc0, cc1 = min(cs), max(cs)
                oh, ow = rr1 - rr0 + 1, cc1 - cc0 + 1
                ch_h, ch_w = r1 - r0 - 1, c1 - c0 - 1
                tr = r0 + 1 + (ch_h - oh) // 2
                tc = c0 + 1 + (ch_w - ow) // 2
                for r, c in cells:
                    nr, nc = tr + (r - rr0), tc + (c - cc0)
                    if not (0 <= nr < h and 0 <= nc < w):
                        return None
                    out[nr][nc] = move
                    if (nr, nc) != (r, c):
                        moved = True
        if not moved and out == inp:
            return None
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("pillar_chamber_center1", make_pillar_chamber_center1())]


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
            "engine": "s2_pillar_chamber_center1",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_pillar_chamber_center1",
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
