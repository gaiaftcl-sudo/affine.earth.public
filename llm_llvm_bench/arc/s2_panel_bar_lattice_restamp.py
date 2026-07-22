"""S2 panel bar-lattice restamp (FoT).

Grammar (same_canvas_rewrite):
  Detect a periodic lattice of HxW panels whose top or bottom edge is a solid
  bar color (long run). Majority-vote a prototype tile across lattice sites,
  force the bar edge, stamp the lattice, and zero everything outside.
  Lattice chosen by maximizing coverage of input nonzero cells.
  Licensed only on perfect train replay.

Canonical close: AGI-2 test task 0607ce86.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _runs_of(row: Sequence[int], col: int) -> List[Tuple[int, int]]:
    out: List[Tuple[int, int]] = []
    i = 0
    n = len(row)
    while i < n:
        if row[i] != col:
            i += 1
            continue
        j = i
        while j < n and row[j] == col:
            j += 1
        out.append((i, j - i))
        i = j
    return out


def _apply(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    total_nz = sum(1 for row in inp for v in row if v)
    if total_nz < 8:
        return None
    best = None
    for bar_col in sorted({v for row in inp for v in row if v}):
        brows = []
        for r in range(h):
            rs = _runs_of(inp[r], bar_col)
            if rs and max(L for _, L in rs) >= 3:
                brows.append(r)
        if len(brows) < 2:
            continue
        gaps = Counter(
            brows[i + 1] - brows[i]
            for i in range(len(brows) - 1)
            if brows[i + 1] - brows[i] >= 3
        )
        if not gaps:
            continue
        for period, _ in gaps.most_common(3):
            brows_set = set(brows)
            chains = []
            for s in brows:
                chain = [s]
                while chain[-1] + period in brows_set:
                    chain.append(chain[-1] + period)
                if len(chain) >= 2:
                    chains.append(chain)
            if not chains:
                continue
            chain = max(chains, key=len)
            rs = _runs_of(inp[chain[0]], bar_col)
            if len(rs) < 2:
                continue
            pw = Counter(L for _, L in rs).most_common(1)[0][0]
            if pw < 3:
                continue
            starts = [s for s, L in rs if L >= pw - 1]
            if len(starts) < 2:
                starts = [s for s, _ in rs]
            if len(starts) < 2:
                continue
            tw = Counter(
                starts[i + 1] - starts[i] for i in range(len(starts) - 1)
            ).most_common(1)[0][0]
            c0 = starts[0]
            starts = []
            c = c0
            while c + pw <= w:
                starts.append(c)
                c += tw
            for gap_try in (1, 2):
                ph = period - gap_try
                if ph < 3:
                    continue
                for mode in ("bottom", "top"):
                    if mode == "bottom":
                        tops = [b - ph + 1 for b in chain if b - ph + 1 >= 0]
                    else:
                        tops = list(chain)
                    tops = [t for t in tops if t + ph <= h]
                    if len(tops) < 2:
                        continue
                    tiles = []
                    for top in tops:
                        for c in starts:
                            if c + pw > w:
                                continue
                            tile = tuple(
                                tuple(inp[top + dr][c + dc] for dc in range(pw))
                                for dr in range(ph)
                            )
                            if any(v != 0 for rowt in tile for v in rowt):
                                tiles.append(tile)
                    if len(tiles) < 4:
                        continue
                    nrs = len(tops)
                    ncs = len(starts)
                    if nrs < 2 or ncs < 2:
                        continue
                    edge_hits = sum(
                        sum(1 for v in (t[0] if mode == "top" else t[-1]) if v == bar_col)
                        for t in tiles
                    )
                    edge_score = edge_hits / (len(tiles) * pw)
                    if edge_score < 0.6:
                        continue
                    proto = [[0] * pw for _ in range(ph)]
                    for dr in range(ph):
                        for dc in range(pw):
                            proto[dr][dc] = Counter(
                                t[dr][dc] for t in tiles
                            ).most_common(1)[0][0]
                    if mode == "bottom":
                        for dc in range(pw):
                            proto[ph - 1][dc] = bar_col
                        content_rows = list(range(ph - 1))
                    else:
                        for dc in range(pw):
                            proto[0][dc] = bar_col
                        content_rows = list(range(1, ph))
                    colors_int = len(
                        {
                            proto[dr][dc]
                            for dr in content_rows
                            for dc in range(pw)
                            if proto[dr][dc] not in (0, bar_col)
                        }
                    )
                    if colors_int < 1:
                        continue
                    covered = 0
                    for r in range(h):
                        for c in range(w):
                            if inp[r][c] == 0:
                                continue
                            if any(
                                top <= r < top + ph and sc <= c < sc + pw
                                for top in tops
                                for sc in starts
                            ):
                                covered += 1
                    coverage = covered / max(1, total_nz)
                    bars_used = len(tops) / len(chain)
                    carg = sum(
                        Counter(t[dr][dc] for t in tiles).most_common(1)[0][1]
                        for dr in content_rows
                        for dc in range(pw)
                    )
                    cscore = carg / (len(tiles) * len(content_rows) * pw)
                    key = (coverage, bars_used, cscore, edge_score, len(tiles), -ph)
                    if best is None or key > best[0]:
                        out = [[0] * w for _ in range(h)]
                        for top in tops:
                            for c in starts:
                                if c + pw > w:
                                    continue
                                for dr in range(ph):
                                    for dc in range(pw):
                                        out[top + dr][c + dc] = proto[dr][dc]
                        best = (key, out)
    return None if best is None else best[1]


def make_panel_bar_lattice_restamp() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _apply(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("panel_bar_lattice_restamp", make_panel_bar_lattice_restamp())]


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
            "engine": "s2_panel_bar_lattice_restamp",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_panel_bar_lattice_restamp",
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
