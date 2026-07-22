"""S2 host accent-align twos stamp (FoT).

Grammar (zoom_in_crop):
  Host = largest same-color 4-connected component; output is its bbox filled
  with host color, keeping any preexisting non-zero cells. Outside the host,
  each 8-connected sprite of color-2 cells plus exactly one accent color is
  translated so that accent aligns with the matching accent already on the
  host; only the 2-cells are painted. Licensed only on perfect train replay.

Canonical close: AGI-2 test task 414297c0.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_N4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_N8 = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc]


def _host_accent_align_twos(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    best: Optional[Tuple[int, int, List[Tuple[int, int]]]] = None
    for r in range(h):
        for c in range(w):
            if inp[r][c] == 0 or seen[r][c]:
                continue
            col = inp[r][c]
            q = deque([(r, c)])
            seen[r][c] = True
            cells: List[Tuple[int, int]] = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in _N4:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and inp[nr][nc] == col:
                        seen[nr][nc] = True
                        q.append((nr, nc))
            if best is None or len(cells) > best[0]:
                best = (len(cells), col, cells)
    if best is None:
        return None
    _, host, hcells = best
    rs = [r for r, _ in hcells]
    cs = [c for _, c in hcells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    oh, ow = r1 - r0 + 1, c1 - c0 + 1
    out = [[host] * ow for _ in range(oh)]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if inp[r][c] != 0:
                out[r - r0][c - c0] = inp[r][c]
    accents_in: Dict[int, List[Tuple[int, int]]] = {}
    for r in range(oh):
        for c in range(ow):
            v = out[r][c]
            if v not in (0, host, 2):
                accents_in.setdefault(v, []).append((r, c))
    seen = [[False] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if inp[r][c] in (0, host) or seen[r][c]:
                continue
            q = deque([(r, c)])
            seen[r][c] = True
            cells2: List[Tuple[int, int, int]] = []
            while q:
                rr, cc = q.popleft()
                cells2.append((rr, cc, inp[rr][cc]))
                for dr, dc in _N8:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and inp[nr][nc] not in (0, host)
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))
            if all(r0 <= rr <= r1 and c0 <= cc <= c1 for rr, cc, _ in cells2):
                continue
            cols = Counter(col for _, _, col in cells2)
            if 2 not in cols:
                continue
            accents = [col for col in cols if col != 2]
            if len(accents) != 1:
                continue
            ac = accents[0]
            if ac not in accents_in:
                continue
            ap = [(rr, cc) for rr, cc, col in cells2 if col == ac]
            ar, ac_ = ap[0]
            hr, hc = accents_in[ac][0]
            tr = r0 + hr - ar
            tc = c0 + hc - ac_
            for rr, cc, col in cells2:
                if col != 2:
                    continue
                pr, pc = rr + tr - r0, cc + tc - c0
                if 0 <= pr < oh and 0 <= pc < ow:
                    out[pr][pc] = 2
    return out


def make_host_accent_align_twos() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _host_accent_align_twos(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("host_accent_align_twos", make_host_accent_align_twos())]


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
            "engine": "s2_host_accent_align_twos",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_host_accent_align_twos",
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
