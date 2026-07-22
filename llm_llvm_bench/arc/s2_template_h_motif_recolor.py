"""S2 template H-motif recolor (FoT).

Grammar (same_canvas_rewrite):
  Background 0, fill 5. A solid rectangular marker template (non-0/non-5) maps
  cell-for-cell onto a same-shape lattice of 4-connected fill=5 H-motifs
  (ordered by motif centers). Each motif is recolored with the matching
  template cell; markers and background stay. Licensed only on perfect train
  replay.

Canonical close: AGI-2 test task 33b52de3.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _comps(g: Grid, pred) -> List[List[Tuple[int, int]]]:
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    out: List[List[Tuple[int, int]]] = []
    for i in range(h):
        for j in range(w):
            if seen[i][j] or not pred(g[i][j]):
                continue
            q = deque([(i, j)])
            seen[i][j] = True
            cells: List[Tuple[int, int]] = []
            while q:
                r, c = q.popleft()
                cells.append((r, c))
                for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < h
                        and 0 <= cc < w
                        and not seen[rr][cc]
                        and pred(g[rr][cc])
                    ):
                        seen[rr][cc] = True
                        q.append((rr, cc))
            out.append(cells)
    return out


def make_template_h_motif_recolor(
    bg: int = 0, fill: int = 5
) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        tcomps = _comps(inp, lambda v: v not in (bg, fill))
        if not tcomps:
            return None
        tmpl = max(tcomps, key=len)
        trs = [r for r, _ in tmpl]
        tcs = [c for _, c in tmpl]
        tr0, tr1, tc0, tc1 = min(trs), max(trs), min(tcs), max(tcs)
        th, tw = tr1 - tr0 + 1, tc1 - tc0 + 1
        if th * tw != len(tmpl):
            return None
        for r in range(tr0, tr1 + 1):
            for c in range(tc0, tc1 + 1):
                if inp[r][c] in (bg, fill):
                    return None
        hs = _comps(inp, lambda v: v == fill)
        if not hs:
            return None
        centers = []
        for cells in hs:
            rs = [r for r, _ in cells]
            cs = [c for _, c in cells]
            centers.append((sum(rs) / len(rs), sum(cs) / len(cs), cells))
        row_keys = sorted({round(cr) for cr, _, _ in centers})
        col_keys = sorted({round(cc) for _, cc, _ in centers})
        if len(row_keys) != th or len(col_keys) != tw:
            return None

        def band(val: float, keys: List[int]) -> int:
            return min(range(len(keys)), key=lambda i: abs(keys[i] - val))

        grid: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
        for cr, cc, cells in centers:
            i, j = band(cr, row_keys), band(cc, col_keys)
            if (i, j) in grid:
                return None
            grid[(i, j)] = cells
        if len(grid) != th * tw:
            return None
        out = [row[:] for row in inp]
        for i in range(th):
            for j in range(tw):
                color = inp[tr0 + i][tc0 + j]
                for r, c in grid[(i, j)]:
                    out[r][c] = color
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("template_h_motif_recolor", make_template_h_motif_recolor())]


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
            "engine": "s2_template_h_motif_recolor",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_template_h_motif_recolor",
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
