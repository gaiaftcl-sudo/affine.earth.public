"""S2 max-gap frame cross (FoT).

Grammar (same_canvas_rewrite):
  Two dominant nonzero colors A,B form a frame around zero cavities.
  On each row, find the longest zero-run bordered on both sides by A/B;
  keep only rows whose gap equals the global max row-gap and paint those
  zeros with 3. Same for columns (max col-gap). Union is a cross/hash of 3s.

Canonical close: AGI-2 test task 2bee17df.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_max_gap_frame_cross(fill: int = 3) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        ctr = Counter(v for row in inp for v in row if v)
        if len(ctr) < 2:
            return None
        a, b = [c for c, _ in ctr.most_common(2)]
        frame = {a, b}

        row_gaps: List[Tuple[int, int, int, int]] = []
        for r in range(h):
            c = 0
            best = 0
            best_seg: Optional[Tuple[int, int]] = None
            while c < w:
                if inp[r][c] != 0:
                    c += 1
                    continue
                c0 = c
                while c < w and inp[r][c] == 0:
                    c += 1
                c1 = c - 1
                left = inp[r][c0 - 1] if c0 > 0 else None
                right = inp[r][c1 + 1] if c1 + 1 < w else None
                if left in frame and right in frame:
                    glen = c1 - c0 + 1
                    if glen > best:
                        best = glen
                        best_seg = (c0, c1)
            if best_seg is not None:
                row_gaps.append((best, r, best_seg[0], best_seg[1]))

        col_gaps: List[Tuple[int, int, int, int]] = []
        for c in range(w):
            r = 0
            best = 0
            best_seg = None
            while r < h:
                if inp[r][c] != 0:
                    r += 1
                    continue
                r0 = r
                while r < h and inp[r][c] == 0:
                    r += 1
                r1 = r - 1
                up = inp[r0 - 1][c] if r0 > 0 else None
                down = inp[r1 + 1][c] if r1 + 1 < h else None
                if up in frame and down in frame:
                    glen = r1 - r0 + 1
                    if glen > best:
                        best = glen
                        best_seg = (r0, r1)
            if best_seg is not None:
                col_gaps.append((best, c, best_seg[0], best_seg[1]))

        if not row_gaps or not col_gaps:
            return None
        max_rg = max(g for g, _, _, _ in row_gaps)
        max_cg = max(g for g, _, _, _ in col_gaps)
        out = [list(row) for row in inp]
        painted = False
        for g, r, c0, c1 in row_gaps:
            if g != max_rg:
                continue
            for c in range(c0, c1 + 1):
                out[r][c] = fill
                painted = True
        for g, c, r0, r1 in col_gaps:
            if g != max_cg:
                continue
            for r in range(r0, r1 + 1):
                out[r][c] = fill
                painted = True
        if not painted or out == inp:
            return None
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("max_gap_frame_cross", make_max_gap_frame_cross())]


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
            "engine": "s2_max_gap_frame_cross",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_max_gap_frame_cross",
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
