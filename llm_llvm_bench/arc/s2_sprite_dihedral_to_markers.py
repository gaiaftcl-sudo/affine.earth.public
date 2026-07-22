"""S2 sprite dihedral-to-markers (FoT).

Grammar (same_canvas_rewrite):
  Multi-color connected sprites (4-connected nonzero) each carry singleton
  key colors (colors with count 1 inside the sprite). Lonely singleton cells
  of those key colors are placement markers. Apply a dihedral transform to
  each sprite, then translate so every key color lands on its marker.
  Output is the placed sprites on a cleared canvas.

Canonical close: AGI-2 test task 0e206a2e.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int, int]


def _comps_any(g: Grid) -> List[List[Cell]]:
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    out: List[List[Cell]] = []
    for i in range(h):
        for j in range(w):
            if seen[i][j] or g[i][j] == 0:
                continue
            q = deque([(i, j)])
            seen[i][j] = True
            cells: List[Cell] = []
            while q:
                r, c = q.popleft()
                cells.append((r, c, g[r][c]))
                for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < h
                        and 0 <= cc < w
                        and not seen[rr][cc]
                        and g[rr][cc] != 0
                    ):
                        seen[rr][cc] = True
                        q.append((rr, cc))
            out.append(cells)
    return out


def _norm(pts: List[Cell]) -> Set[Cell]:
    rs = [r for r, _, _ in pts]
    cs = [c for _, c, _ in pts]
    r0, c0 = min(rs), min(cs)
    return {(r - r0, c - c0, v) for r, c, v in pts}


def _dihedral(cells: List[Cell]) -> List[Set[Cell]]:
    variants: List[Set[Cell]] = []
    cur = list(cells)
    for _ in range(4):
        variants.append(_norm(cur))
        cur = [(c, -r, v) for r, c, v in cur]
    cur = [(r, -c, v) for r, c, v in cells]
    for _ in range(4):
        variants.append(_norm(cur))
        cur = [(c, -r, v) for r, c, v in cur]
    return variants


def make_sprite_dihedral_to_markers() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        objs = _comps_any(inp)
        sprites = [o for o in objs if len(o) > 1]
        singles = [o[0] for o in objs if len(o) == 1]
        if not sprites or not singles:
            return None
        out = [[0] * w for _ in range(h)]
        placed_any = False
        used: Set[Tuple[int, int]] = set()
        for sprite in sprites:
            cnt = Counter(v for _, _, v in sprite)
            keys = [c for c, n in cnt.items() if n == 1]
            markers = {
                v: (r, c)
                for r, c, v in singles
                if v in keys and (r, c) not in used
            }
            if not markers:
                continue
            best: Optional[List[Cell]] = None
            for var in _dihedral(sprite):
                key_pos = {v: (r, c) for r, c, v in var if v in markers}
                if not key_pos:
                    continue
                k = next(iter(key_pos))
                sr, sc = key_pos[k]
                mr, mc = markers[k]
                dr, dc = mr - sr, mc - sc
                if any(
                    (sr2 + dr, sc2 + dc) != markers[k2]
                    for k2, (sr2, sc2) in key_pos.items()
                    if k2 in markers
                ):
                    continue
                placed: List[Cell] = []
                good = True
                for r, c, v in var:
                    rr, cc = r + dr, c + dc
                    if not (0 <= rr < h and 0 <= cc < w):
                        good = False
                        break
                    placed.append((rr, cc, v))
                if good:
                    best = placed
                    break
            if best is None:
                continue
            for r, c, v in best:
                out[r][c] = v
                placed_any = True
            for pos in markers.values():
                used.add(pos)
        return out if placed_any else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("sprite_dihedral_to_markers", make_sprite_dihedral_to_markers())]


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
            "engine": "s2_sprite_dihedral_to_markers",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_sprite_dihedral_to_markers",
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
