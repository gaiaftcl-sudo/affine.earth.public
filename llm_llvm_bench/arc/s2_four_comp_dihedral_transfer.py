"""S2 four-comp dihedral transfer (FoT).

Grammar (same_canvas_rewrite):
  Color-4 cells form several equal components. One source component is already
  decorated with colors 1 and 3 (and a single orientation marker 2). Each other
  component carries only a 2. Find a dihedral map taking the source 4-shape onto
  the target 4-shape that also sends the source 2 onto the target 2, then paint
  the mapped 1/3 marks into empty cells around the target.

Canonical close: AGI-2 test task 36d67576.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]


def _comps(inp: Grid, col: int) -> List[List[Cell]]:
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    out: List[List[Cell]] = []
    for r in range(h):
        for c in range(w):
            if inp[r][c] != col or seen[r][c]:
                continue
            q = deque([(r, c)])
            seen[r][c] = True
            cells: List[Cell] = []
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and not seen[nx][ny]
                        and inp[nx][ny] == col
                    ):
                        seen[nx][ny] = True
                        q.append((nx, ny))
            out.append(cells)
    return out


def _normalize(cells: Sequence[Cell]) -> Tuple[frozenset, int, int]:
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells), r0, c0


def _all_dihedral() -> List[Callable[[int, int], Cell]]:
    def rot90(r: int, c: int) -> Cell:
        return (-c, r)

    def compose(f, g):  # noqa: ANN001
        return lambda r, c, f=f, g=g: f(*g(r, c))

    identity = lambda r, c: (r, c)
    transforms: List[Callable[[int, int], Cell]] = []
    cur = identity
    for _ in range(4):
        transforms.append(cur)
        transforms.append(compose(lambda r, c: (r, -c), cur))
        cur = compose(rot90, cur)
    return transforms


def make_four_comp_dihedral_transfer(
    wall: int = 4, paints: Tuple[int, ...] = (1, 3), orient: int = 2
) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        comps = _comps(inp, wall)
        if len(comps) < 2:
            return None

        def near_marks(cells: Sequence[Cell]) -> List[Tuple[int, int, int]]:
            marks: List[Tuple[int, int, int]] = []
            for r in range(h):
                for c in range(w):
                    v = inp[r][c]
                    if v not in paints and v != orient:
                        continue
                    if min(max(abs(r - x), abs(c - y)) for x, y in cells) <= 2:
                        marks.append((r, c, v))
            return marks

        meta = []
        for cells in comps:
            shape, r0, c0 = _normalize(cells)
            marks = near_marks(cells)
            rel = [(r - r0, c - c0, v) for r, c, v in marks]
            meta.append(
                {"shape": shape, "r0": r0, "c0": c0, "marks": rel}
            )

        src = None
        for m in meta:
            vals = {v for _, _, v in m["marks"]}
            if all(p in vals for p in paints):
                src = m
                break
        if src is None:
            return None
        src_twos = [(r, c) for r, c, v in src["marks"] if v == orient]
        src_paint = [(r, c, v) for r, c, v in src["marks"] if v in paints]
        if len(src_twos) != 1 or not src_paint:
            return None
        s2 = src_twos[0]
        out = [list(row) for row in inp]
        painted = False
        fns = _all_dihedral()
        for m in meta:
            if m is src:
                continue
            twos = [(r, c) for r, c, v in m["marks"] if v == orient]
            if len(twos) != 1:
                continue
            t2 = twos[0]
            found = None
            for fn in fns:
                img = frozenset(fn(r, c) for r, c in src["shape"])
                ir0 = min(r for r, _ in img)
                ic0 = min(c for _, c in img)
                key = frozenset((r - ir0, c - ic0) for r, c in img)
                if key != m["shape"]:
                    continue
                rr, cc = fn(s2[0], s2[1])
                rr -= ir0
                cc -= ic0
                if (rr, cc) == t2:
                    found = (fn, ir0, ic0)
                    break
            if found is None:
                continue
            fn, ir0, ic0 = found
            for r, c, v in src_paint:
                rr, cc = fn(r, c)
                rr -= ir0
                cc -= ic0
                ar, ac = m["r0"] + rr, m["c0"] + cc
                if 0 <= ar < h and 0 <= ac < w and out[ar][ac] == 0:
                    out[ar][ac] = v
                    painted = True
        if not painted:
            return None
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("four_comp_dihedral_transfer", make_four_comp_dihedral_transfer())]


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
            "engine": "s2_four_comp_dihedral_transfer",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, _ = exact[0]
    passed = len(train)
    return {
        "engine": "s2_four_comp_dihedral_transfer",
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
