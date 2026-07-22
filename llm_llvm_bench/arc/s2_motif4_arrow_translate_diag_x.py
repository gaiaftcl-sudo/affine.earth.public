"""S2 motif4 arrow-translate diagonal X (FoT).

Grammar (same_canvas_rewrite):
  Find a 3x3 ring of color 4 whose center is a nonzero non-4 fill color.
  A singleton of that fill color (seed) and a singleton exterior 4 (tip)
  define a translation delta = tip - seed. Translate the motif by delta,
  fill the canvas with the fill color, stamp the motif, and paint both
  full diagonals of 4 through the new motif center. Licensed only on
  perfect train replay.

Canonical close: AGI-2 test task 2b9ef948.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _apply(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    motif = None
    for r in range(h - 2):
        for c in range(w - 2):
            vals = [inp[r + dr][c + dc] for dr in range(3) for dc in range(3)]
            if all(vals[i] == 4 for i in (0, 1, 2, 3, 5, 6, 7, 8)) and vals[4] not in (0, 4):
                motif = (r, c, vals[4])
                break
        if motif:
            break
    if not motif:
        return None
    mr, mc, fill = motif
    seeds = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if inp[r][c] == fill and not (r == mr + 1 and c == mc + 1)
    ]
    tips = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if inp[r][c] == 4 and not (mr <= r <= mr + 2 and mc <= c <= mc + 2)
    ]
    if len(seeds) != 1 or len(tips) != 1:
        return None
    sr, sc = seeds[0]
    tr, tc = tips[0]
    dr, dc = tr - sr, tc - sc
    nmr, nmc = mr + dr, mc + dc
    if not (0 <= nmr and nmr + 2 < h and 0 <= nmc and nmc + 2 < w):
        return None
    out = [[fill] * w for _ in range(h)]
    cr, cc = nmr + 1, nmc + 1
    span = max(h, w)
    for k in range(-span, span + 1):
        for rr, cc2 in ((cr + k, cc + k), (cr + k, cc - k)):
            if 0 <= rr < h and 0 <= cc2 < w:
                out[rr][cc2] = 4
    for i in range(3):
        for j in range(3):
            out[nmr + i][nmc + j] = fill if (i, j) == (1, 1) else 4
    return out


def make_motif4_arrow_translate_diag_x() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _apply(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("motif4_arrow_translate_diag_x", make_motif4_arrow_translate_diag_x())]


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
            "engine": "s2_motif4_arrow_translate_diag_x",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_motif4_arrow_translate_diag_x",
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
