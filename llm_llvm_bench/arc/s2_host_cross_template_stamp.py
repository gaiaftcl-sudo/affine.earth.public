"""S2 host-cross template stamp (FoT).

Grammar (same_canvas_rewrite):
  Second-most-common color is the host field; rare off-host cells form a
  marker template whose center color also appears as on-host seeds. Erase the
  off-host template to background. For each on-host center seed, stamp the
  relative template into its host component. Extend the pure-vertical axis
  color through the host column; also extend the host row when that color
  matches the pure-horizontal axis color (unified plus). Licensed only on
  perfect train replay.

Canonical close: AGI-2 test task 264363fd.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _host_components(inp: Grid, host: int) -> List[set]:
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    comps: List[set] = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or inp[r][c] != host:
                continue
            cells: List[Tuple[int, int]] = []
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and inp[nr][nc] == host
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))
            comps.append(set(cells))
    return comps


def _apply(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    cnt = Counter(v for row in inp for v in row)
    if len(cnt) < 3:
        return None
    bg = cnt.most_common(1)[0][0]
    host = cnt.most_common(2)[1][0]
    rares = {c for c in cnt if c not in (bg, host)}
    if not rares:
        return None
    comps = _host_components(inp, host)
    if not comps:
        return None
    on_host: List[Tuple[int, int, int]] = []
    off_host: List[Tuple[int, int, int]] = []
    for r in range(h):
        for c in range(w):
            col = inp[r][c]
            if col not in rares:
                continue
            if any(
                0 <= r + dr < h
                and 0 <= c + dc < w
                and inp[r + dr][c + dc] == host
                for dr, dc in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                on_host.append((r, c, col))
            else:
                off_host.append((r, c, col))
    if not on_host or not off_host:
        return None
    center_col = Counter(c for _, _, c in on_host).most_common(1)[0][0]
    tcenters = [(r, c) for r, c, col in off_host if col == center_col]
    if not tcenters:
        return None
    rs = [r for r, _, _ in off_host]
    cs = [c for _, c, _ in off_host]
    gr = (min(rs) + max(rs)) / 2
    gc = (min(cs) + max(cs)) / 2
    tr0, tc0 = min(tcenters, key=lambda p: (p[0] - gr) ** 2 + (p[1] - gc) ** 2)
    rel = [(r - tr0, c - tc0, col) for r, c, col in off_host]
    specials = [(r, c) for r, c, col in on_host if col == center_col]
    if not specials:
        return None
    vert_cols = [col for dr, dc, col in rel if dc == 0 and dr != 0]
    horiz_cols = [col for dr, dc, col in rel if dr == 0 and dc != 0]
    vert_col = Counter(vert_cols).most_common(1)[0][0] if vert_cols else None
    horiz_col = Counter(horiz_cols).most_common(1)[0][0] if horiz_cols else None
    out = [row[:] for row in inp]
    for r, c, _ in off_host:
        out[r][c] = bg
    changed = False
    for sr, sc in specials:
        target = None
        for cells in comps:
            if any(abs(r - sr) + abs(c - sc) == 1 for r, c in cells):
                target = cells
                break
        if target is None:
            for cells in comps:
                crs = [r for r, _ in cells]
                ccs = [c for _, c in cells]
                if min(crs) <= sr <= max(crs) and min(ccs) <= sc <= max(ccs):
                    target = cells
                    break
        if target is None:
            continue
        if vert_col is not None:
            for r, c in target:
                if c == sc and out[r][c] != vert_col:
                    out[r][c] = vert_col
                    changed = True
        if horiz_col is not None and horiz_col == vert_col:
            for r, c in target:
                if r == sr and out[r][c] != horiz_col:
                    out[r][c] = horiz_col
                    changed = True
        for dr, dc, col in rel:
            nr, nc = sr + dr, sc + dc
            if 0 <= nr < h and 0 <= nc < w and ((nr, nc) in target or (nr, nc) == (sr, sc)):
                if out[nr][nc] != col:
                    out[nr][nc] = col
                    changed = True
        if out[sr][sc] != center_col:
            out[sr][sc] = center_col
            changed = True
    return out if changed else None


def make_host_cross_template_stamp() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _apply(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("host_cross_template_stamp", make_host_cross_template_stamp())]


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
            "engine": "s2_host_cross_template_stamp",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_host_cross_template_stamp",
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
