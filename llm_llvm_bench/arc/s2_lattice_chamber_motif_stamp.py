"""S2 lattice chamber motif stamp (FoT).

Grammar (same_canvas_rewrite):
  Lattice color = color that forms at least one full row. Full lattice rows and
  the vertical lattice pillars that span every non-full-row cell partition the
  canvas into chambers. Marker color = the other nonzero color. Take the
  largest 8-connected marker component as the motif (normalized to its bbox
  origin). Stamp that motif, centered, into every chamber by painting lattice
  onto zeros (markers preserved).

Canonical close: AGI-2 test task 1e32b0e9.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _comps8(g: Grid, keep) -> List[List[Tuple[int, int]]]:
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    out: List[List[Tuple[int, int]]] = []
    for i in range(h):
        for j in range(w):
            if seen[i][j] or not keep(g[i][j]):
                continue
            q = deque([(i, j)])
            seen[i][j] = True
            cells: List[Tuple[int, int]] = []
            while q:
                r, c = q.popleft()
                cells.append((r, c))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        rr, cc = r + dr, c + dc
                        if (
                            0 <= rr < h
                            and 0 <= cc < w
                            and not seen[rr][cc]
                            and keep(g[rr][cc])
                        ):
                            seen[rr][cc] = True
                            q.append((rr, cc))
            out.append(cells)
    return out


def make_lattice_chamber_motif_stamp() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        cnt = Counter(v for row in inp for v in row if v)
        if len(cnt) < 2:
            return None
        lattice = None
        for col, _ in cnt.most_common():
            if any(all(cell == col for cell in row) for row in inp):
                lattice = col
                break
        if lattice is None:
            return None
        full_rows = sorted(
            r for r in range(h) if all(inp[r][c] == lattice for c in range(w))
        )
        full_row_set = set(full_rows)
        full_cols = sorted(
            c
            for c in range(w)
            if all(inp[r][c] == lattice for r in range(h) if r not in full_row_set)
        )
        if not full_rows or not full_cols:
            return None
        markers = [v for v in cnt if v != lattice]
        if not markers:
            return None
        mcol = min(markers, key=lambda v: cnt[v])
        mcomps = _comps8(inp, lambda v, m=mcol: v == m)
        if not mcomps:
            return None
        cells = max(mcomps, key=len)
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r0, c0 = min(rs), min(cs)
        motif = sorted((r - r0, c - c0) for r, c in cells)
        mh = max(r for r, _ in motif) + 1
        mw = max(c for _, c in motif) + 1
        row_bounds = [-1] + full_rows + [h]
        col_bounds = [-1] + full_cols + [w]
        out = [row[:] for row in inp]
        stamped = False
        for i in range(len(row_bounds) - 1):
            ar0, ar1 = row_bounds[i] + 1, row_bounds[i + 1] - 1
            if ar0 > ar1:
                continue
            for j in range(len(col_bounds) - 1):
                ac0, ac1 = col_bounds[j] + 1, col_bounds[j + 1] - 1
                if ac0 > ac1:
                    continue
                ch_h = ar1 - ar0 + 1
                ch_w = ac1 - ac0 + 1
                off_r = ar0 + (ch_h - mh) // 2
                off_c = ac0 + (ch_w - mw) // 2
                for dr, dc in motif:
                    r, c = off_r + dr, off_c + dc
                    if ar0 <= r <= ar1 and ac0 <= c <= ac1 and out[r][c] == 0:
                        out[r][c] = lattice
                        stamped = True
        if not stamped:
            return None
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("lattice_chamber_motif_stamp", make_lattice_chamber_motif_stamp())]


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
            "engine": "s2_lattice_chamber_motif_stamp",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_lattice_chamber_motif_stamp",
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
