"""S2 five-mask exact cover: 2x2 eights + straight-tromino twos (FoT).

Grammar (same_canvas_rewrite):
  Mask color 5 on background 0. Partition the mask into 2x2 squares (paint 8)
  and straight trominoes (paint 2). Among exact covers, maximize the number of
  2x2 squares (unique on train and the held-out test shape).

Canonical close: AGI-2 test task 150deff5.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]
Part = Tuple[str, Tuple[Cell, ...]]


def _mask_cells(inp: Grid, mask: int = 5) -> List[Cell]:
    return [
        (r, c)
        for r in range(len(inp))
        for c in range(len(inp[0]))
        if inp[r][c] == mask
    ]


def _parts(cells: Sequence[Cell]) -> List[Tuple[str, Tuple[Cell, ...], int]]:
    S = set(cells)
    idx = {cell: i for i, cell in enumerate(cells)}
    out: List[Tuple[str, Tuple[Cell, ...], int]] = []
    for r, c in cells:
        for tri in (
            ((r, c), (r, c + 1), (r, c + 2)),
            ((r, c), (r + 1, c), (r + 2, c)),
        ):
            if all(x in S for x in tri):
                bits = 0
                for x in tri:
                    bits |= 1 << idx[x]
                out.append(("T", tri, bits))
        sq = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
        if all(x in S for x in sq):
            bits = 0
            for x in sq:
                bits |= 1 << idx[x]
            out.append(("S", sq, bits))
    return out


def _paint(inp: Grid, partition: Sequence[Part], tile: int = 8, rest: int = 2) -> Grid:
    h, w = len(inp), len(inp[0])
    out = [[0] * w for _ in range(h)]
    for kind, cells in partition:
        color = tile if kind == "S" else rest
        for r, c in cells:
            out[r][c] = color
    return out


def _solve_partition(inp: Grid, mask: int = 5) -> Optional[Grid]:
    cells = _mask_cells(inp, mask=mask)
    n = len(cells)
    if n == 0:
        return [list(row) for row in inp]
    parts = _parts(cells)
    best: List[List[Part]] = []
    best_s = -1
    full = (1 << n) - 1

    def bt(covered: int, chosen: List[Part], n_s: int) -> None:
        nonlocal best, best_s
        if covered == full:
            if n_s > best_s:
                best_s = n_s
                best = [list(chosen)]
            elif n_s == best_s:
                best.append(list(chosen))
            return
        b = 0
        while covered & (1 << b):
            b += 1
        for kind, tiles, bits in parts:
            if (bits & (1 << b)) == 0:
                continue
            if bits & covered:
                continue
            chosen.append((kind, tiles))
            bt(covered | bits, chosen, n_s + (1 if kind == "S" else 0))
            chosen.pop()

    bt(0, [], 0)
    if not best:
        return None
    uniq: Dict[Tuple[Tuple[int, ...], ...], Grid] = {}
    for part in best:
        g = _paint(inp, part)
        uniq[tuple(tuple(row) for row in g)] = g
    if len(uniq) != 1:
        return None
    return next(iter(uniq.values()))


def make_five_pack_tromino2(mask: int = 5) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        if any(v not in (0, mask) for row in inp for v in row):
            return None
        return _solve_partition(inp, mask=mask)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("five_pack_tromino2", make_five_pack_tromino2())]


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
            "engine": "s2_five_pack_tromino2",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_five_pack_tromino2",
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
