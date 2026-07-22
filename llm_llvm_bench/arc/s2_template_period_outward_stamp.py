"""S2 template period outward stamp (FoT).

Grammar (same_canvas_rewrite):
  Template color = nonzero color with the most cells; its cells are the motif
  (bbox-normalized). Each other color forms 8-connected marker groups. For each
  marker group, direction is the sign of (marker_centroid - template_centroid)
  on each axis. Align the motif so markers are a subset of the painted stamp and
  the stamp extends outward along that direction, then tile the motif in the
  marker color with period = max(motif_h, motif_w) + 1, filling zeros only.

Canonical close: AGI-2 test task 045e512c.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_template_period_outward_stamp(bg: int = 0) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        cnt = Counter(v for row in inp for v in row if v != bg)
        if len(cnt) < 2:
            return None
        tcol = max(cnt, key=lambda c: (cnt[c], c))
        tcells = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == tcol]
        if not tcells:
            return None
        trs = [r for r, _ in tcells]
        tcs = [c for _, c in tcells]
        tr0, tc0 = min(trs), min(tcs)
        motif = [(r - tr0, c - tc0) for r, c in tcells]
        th = max(r for r, _ in motif) + 1
        tw = max(c for _, c in motif) + 1
        tcr = (min(trs) + max(trs)) / 2.0
        tcc = (min(tcs) + max(tcs)) / 2.0
        period = max(th, tw) + 1
        out = [row[:] for row in inp]
        changed = False

        def comps8(col: int) -> List[List[Tuple[int, int]]]:
            seen = set()
            groups: List[List[Tuple[int, int]]] = []
            for r in range(h):
                for c in range(w):
                    if inp[r][c] != col or (r, c) in seen:
                        continue
                    q = deque([(r, c)])
                    seen.add((r, c))
                    cells: List[Tuple[int, int]] = []
                    while q:
                        rr, cc = q.popleft()
                        cells.append((rr, cc))
                        for dr in (-1, 0, 1):
                            for dc in (-1, 0, 1):
                                if dr == 0 and dc == 0:
                                    continue
                                nr, nc = rr + dr, cc + dc
                                if (
                                    0 <= nr < h
                                    and 0 <= nc < w
                                    and inp[nr][nc] == col
                                    and (nr, nc) not in seen
                                ):
                                    seen.add((nr, nc))
                                    q.append((nr, nc))
                    groups.append(cells)
            return groups

        for col in cnt:
            if col == tcol:
                continue
            for cells in comps8(col):
                cellset = set(cells)
                mrs = [r for r, _ in cells]
                mcs = [c for _, c in cells]
                mcr = sum(mrs) / len(mrs)
                mcc = sum(mcs) / len(mcs)
                dr = 0 if abs(mcr - tcr) < 0.51 else (1 if mcr > tcr else -1)
                dc = 0 if abs(mcc - tcc) < 0.51 else (1 if mcc > tcc else -1)
                if dr == 0 and dc == 0:
                    br = max(mrs) - min(mrs) + 1
                    bc = max(mcs) - min(mcs) + 1
                    if bc >= br:
                        dr = 1 if mcr >= tcr else -1
                    else:
                        dc = 1 if mcc >= tcc else -1
                cands: List[Tuple[float, float, int, int]] = []
                for mr0, mc0 in motif:
                    for r, c in cells:
                        ar, ac = r - mr0, c - mc0
                        painted = {(ar + mr, ac + mc) for mr, mc in motif}
                        if not cellset <= painted:
                            continue
                        prs = [ar + mr for mr, _ in motif]
                        pcs = [ac + mc for _, mc in motif]
                        scr = sum(prs) / len(prs)
                        scc = sum(pcs) / len(pcs)
                        out_score = (scr - mcr) * dr + (scc - mcc) * dc
                        far = (scr - tcr) * dr + (scc - tcc) * dc
                        cands.append((-out_score, -far, ar, ac))
                if not cands:
                    continue
                cands.sort()
                _, _, ar, ac = cands[0]
                k = 0
                while k < 16:
                    r0 = ar + k * period * dr
                    c0 = ac + k * period * dc
                    any_in = False
                    for mr, mc in motif:
                        r, c = r0 + mr, c0 + mc
                        if 0 <= r < h and 0 <= c < w:
                            any_in = True
                            if out[r][c] == bg:
                                out[r][c] = col
                                changed = True
                    if not any_in and k > 0:
                        break
                    if dr == 0 and dc == 0:
                        break
                    k += 1
        return out if changed else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("template_period_outward_stamp", make_template_period_outward_stamp())]


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
            "engine": "s2_template_period_outward_stamp",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, _ = exact[0]
    passed = len(train)
    return {
        "engine": "s2_template_period_outward_stamp",
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
