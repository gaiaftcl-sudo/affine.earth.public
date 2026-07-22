"""S2 lattice hub halo stamp (FoT).

Grammar (same_canvas_rewrite):
  Full-line separator color partitions the canvas into a lattice of chambers.
  Solid non-separator chambers are hubs/fill. Find the solid chamber with the
  richest Chebyshev halo of other solid colors (plus or full ring; possibly
  multi-color). That chamber's color is the hub. Stamp the same relative
  offset→color halo into empty chambers around every hub of that color.
  Licensed only on perfect train replay.

Canonical close: AGI-2 test task 39e1d7f9.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _parse_lattice(inp: Grid) -> Optional[Tuple[int, Dict[Tuple[int, int], Tuple[int, int, Grid]]]]:
    h, w = len(inp), len(inp[0])
    sep = None
    srows: List[int] = []
    scols: List[int] = []
    for cand in range(1, 10):
        srows = [r for r in range(h) if all(inp[r][c] == cand for c in range(w))]
        scols = [c for c in range(w) if all(inp[r][c] == cand for r in range(h))]
        if len(srows) >= 2 and len(scols) >= 2:
            sep = cand
            break
    if sep is None:
        return None
    rs = [-1] + srows + [h]
    cs = [-1] + scols + [w]
    tiles: Dict[Tuple[int, int], Tuple[int, int, Grid]] = {}
    for i in range(len(rs) - 1):
        r0, r1 = rs[i] + 1, rs[i + 1] - 1
        if r0 > r1:
            continue
        for j in range(len(cs) - 1):
            c0, c1 = cs[j] + 1, cs[j + 1] - 1
            if c0 > c1:
                continue
            block = [list(inp[r][c0 : c1 + 1]) for r in range(r0, r1 + 1)]
            tiles[(i, j)] = (r0, c0, block)
    if not tiles:
        return None
    return sep, tiles


def _tile_mode(block: Grid) -> Optional[int]:
    vals = [v for row in block for v in row]
    if not vals:
        return None
    if all(v == 0 for v in vals):
        return 0
    nz = [v for v in vals if v != 0]
    if nz and all(v == nz[0] for v in nz) and len(nz) == len(vals):
        return nz[0]
    return None


def make_lattice_hub_halo_stamp() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        parsed = _parse_lattice(inp)
        if parsed is None:
            return None
        sep, tiles = parsed
        modes = {k: _tile_mode(block) for k, (_, _, block) in tiles.items()}
        solids = {
            k: m
            for k, m in modes.items()
            if isinstance(m, int) and m not in (0, sep)
        }
        empties = {k for k, m in modes.items() if m == 0}
        if len(solids) < 2:
            return None
        best_n = -1
        hub_col: Optional[int] = None
        template: Dict[Tuple[int, int], int] = {}
        for (i, j), col in solids.items():
            offs: Dict[Tuple[int, int], int] = {}
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    if di == 0 and dj == 0:
                        continue
                    nb = (i + di, j + dj)
                    if nb in solids and solids[nb] != col:
                        offs[(di, dj)] = solids[nb]
            if len(offs) > best_n:
                best_n = len(offs)
                hub_col = col
                template = offs
        if hub_col is None or not template:
            return None
        hubs = [k for k, m in solids.items() if m == hub_col]
        out = [row[:] for row in inp]
        for i, j in hubs:
            for (di, dj), fcol in template.items():
                nb = (i + di, j + dj)
                if nb not in empties:
                    continue
                r0, c0, block = tiles[nb]
                for dr, row in enumerate(block):
                    for dc in range(len(row)):
                        out[r0 + dr][c0 + dc] = fcol
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("lattice_hub_halo_stamp", make_lattice_hub_halo_stamp())]


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
            "engine": "s2_lattice_hub_halo_stamp",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_lattice_hub_halo_stamp",
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
