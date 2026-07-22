"""S2 stamp unique-color motif with learned dihedral (FoT).

Grammar (same_canvas_rewrite):
  8-connected non-background blobs: multi-cell blobs are templates; singleton
  blobs are markers. For each template, the unique color (count == 1) that also
  appears as a singleton marker is the anchor. Learn a per-anchor-color dihedral
  from train (intersection of transforms that stamp every marker correctly),
  preference order id/fh/rot90/.... At test time, stamp each template onto all
  matching markers using the learned dihedral.

Canonical close: AGI-2 test task 3e980e27.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_TRANS: Dict[str, Callable[[int, int], Tuple[int, int]]] = {
    "id": lambda r, c: (r, c),
    "rot90": lambda r, c: (-c, r),
    "rot180": lambda r, c: (-r, -c),
    "rot270": lambda r, c: (c, -r),
    "fh": lambda r, c: (r, -c),
    "fv": lambda r, c: (-r, c),
    "ft": lambda r, c: (c, r),
    "fanti": lambda r, c: (-c, -r),
}
_PREF = ["id", "fh", "rot90", "rot270", "fv", "rot180", "ft", "fanti"]


def _comps(inp: Grid, bg: int = 0) -> List[List[Tuple[int, int, int]]]:
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    deltas = [
        (dr, dc)
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if not (dr == 0 and dc == 0)
    ]
    out: List[List[Tuple[int, int, int]]] = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or inp[r][c] == bg:
                continue
            q = deque([(r, c)])
            seen[r][c] = True
            cells: List[Tuple[int, int, int]] = []
            while q:
                x, y = q.popleft()
                cells.append((x, y, inp[x][y]))
                for dx, dy in deltas:
                    xx, yy = x + dx, y + dy
                    if (
                        0 <= xx < h
                        and 0 <= yy < w
                        and not seen[xx][yy]
                        and inp[xx][yy] != bg
                    ):
                        seen[xx][yy] = True
                        q.append((xx, yy))
            out.append(cells)
    return out


def _working_maps(inp: Grid, out: Grid) -> Dict[int, set]:
    h, w = len(inp), len(inp[0])
    cs = _comps(inp)
    multis = [c for c in cs if len(c) > 1]
    singles = [c[0] for c in cs if len(c) == 1]
    result: Dict[int, set] = defaultdict(set)
    for templ in multis:
        colors = Counter(v for *_, v in templ)
        for acol, cnt in colors.items():
            if cnt != 1:
                continue
            markers = [(r, c) for r, c, v in singles if v == acol]
            if not markers:
                continue
            anchors = [(r, c) for r, c, v in templ if v == acol]
            for tname, tfn in _TRANS.items():
                for ar, ac in anchors:
                    rel = [
                        (tfn(r - ar, c - ac)[0], tfn(r - ar, c - ac)[1], v)
                        for r, c, v in templ
                    ]
                    ok = True
                    for mr, mc in markers:
                        for dr, dc, v in rel:
                            rr, cc = mr + dr, mc + dc
                            if not (0 <= rr < h and 0 <= cc < w) or out[rr][cc] != v:
                                ok = False
                                break
                        if not ok:
                            break
                    if ok:
                        result[acol].add(tname)
                        break
    return result


def _learn_cmap(train: Sequence[Dict[str, Any]]) -> Optional[Dict[int, str]]:
    inter: Dict[int, set] = {}
    for ex in train:
        wm = _working_maps(ex["input"], ex["output"])
        if not wm:
            return None
        for k, v in wm.items():
            if k in inter:
                inter[k] &= set(v)
            else:
                inter[k] = set(v)
    if not inter:
        return None
    cmap: Dict[int, str] = {}
    for k, v in inter.items():
        if not v:
            return None
        for p in _PREF:
            if p in v:
                cmap[k] = p
                break
        else:
            cmap[k] = sorted(v)[0]
    return cmap


def make_stamp_unique_color_dihedral(cmap: Dict[int, str]) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0] or not cmap:
            return None
        h, w = len(inp), len(inp[0])
        cs = _comps(inp)
        multis = [c for c in cs if len(c) > 1]
        singles = [c[0] for c in cs if len(c) == 1]
        out = [list(row) for row in inp]
        did = False
        for templ in multis:
            colors = Counter(v for *_, v in templ)
            for acol, cnt in colors.items():
                if cnt != 1 or acol not in cmap:
                    continue
                markers = [(r, c) for r, c, v in singles if v == acol]
                if not markers:
                    continue
                tfn = _TRANS[cmap[acol]]
                anchors = [(r, c) for r, c, v in templ if v == acol]
                for ar, ac in anchors:
                    rel = [
                        (tfn(r - ar, c - ac)[0], tfn(r - ar, c - ac)[1], v)
                        for r, c, v in templ
                    ]
                    if all(
                        0 <= mr + dr < h and 0 <= mc + dc < w
                        for mr, mc in markers
                        for dr, dc, _ in rel
                    ):
                        for mr, mc in markers:
                            for dr, dc, v in rel:
                                out[mr + dr][mc + dc] = v
                        did = True
                        break
        return out if did else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    if not train:
        return []
    cmap = _learn_cmap(train)
    if not cmap:
        return []
    return [("stamp_unique_color_dihedral", make_stamp_unique_color_dihedral(cmap))]


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
            "engine": "s2_stamp_unique_color_dihedral",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_stamp_unique_color_dihedral",
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
