"""S2 sprite magnet reseat (FoT).

Grammar (same_canvas_rewrite):
  Background = mode color. Multi-cell non-bg components are sprites; singleton
  non-bg cells are magnets/markers. A sprite's key is a color that appears once
  inside it and also as an external singleton; reseat the sprite so that key
  lands on every such magnet (satellites within Chebyshev≤2 of the key move
  with it). Sprites without a key align above same-column host magnets (host
  color below the sprite); magnets with a 5 below them in-column are skipped.
  Licensed only on perfect train replay.

Canonical close: AGI-2 test task 1b59e163.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _comps_nonbg(g: Grid, bg: int) -> List[List[Tuple[int, int]]]:
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    out: List[List[Tuple[int, int]]] = []
    for i in range(h):
        for j in range(w):
            if seen[i][j] or g[i][j] == bg:
                continue
            q = deque([(i, j)])
            seen[i][j] = True
            cells: List[Tuple[int, int]] = []
            while q:
                r, c = q.popleft()
                cells.append((r, c))
                for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < h
                        and 0 <= cc < w
                        and not seen[rr][cc]
                        and g[rr][cc] != bg
                    ):
                        seen[rr][cc] = True
                        q.append((rr, cc))
            out.append(cells)
    return out


def make_sprite_magnet_reseat() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        bg = Counter(v for row in inp for v in row).most_common(1)[0][0]
        comps = _comps_nonbg(inp, bg)
        singles: List[Tuple[int, int]] = []
        sprites: List[List[Tuple[int, int]]] = []
        for cells in comps:
            if len(cells) == 1:
                singles.append(cells[0])
            else:
                sprites.append(cells)
        if not sprites:
            return None
        single_by_col: Dict[int, List[Tuple[int, int]]] = {}
        for r, c in singles:
            single_by_col.setdefault(inp[r][c], []).append((r, c))
        fives = single_by_col.get(5, [])
        killed: Set[Tuple[int, int]] = set()
        for fr, fc in fives:
            for col, positions in list(single_by_col.items()):
                if col == 5:
                    continue
                for pr, pc in positions:
                    if pc == fc and pr < fr:
                        killed.add((pr, pc))

        out = [[bg] * w for _ in range(h)]
        placed_any = False
        for cells in sprites:
            colors = Counter(inp[r][c] for r, c in cells)
            cell_set = set(cells)
            key_cands = [
                col
                for col, n in colors.items()
                if n == 1
                and col != 5
                and col in single_by_col
                and any(p not in cell_set for p in single_by_col[col])
            ]
            if key_cands:
                key = key_cands[0]
                ar, ac = next((r, c) for r, c in cells if inp[r][c] == key)
                targets = [p for p in single_by_col[key] if p not in cell_set]
                sats = [
                    (r, c)
                    for r, c in singles
                    if inp[r][c] not in (5, key)
                    and max(abs(r - ar), abs(c - ac)) <= 2
                    and (r, c) not in cell_set
                ]
                if not targets:
                    return None
                for tr, tc in targets:
                    dr, dc = tr - ar, tc - ac
                    for r, c in cells:
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < h and 0 <= cc < w:
                            out[rr][cc] = inp[r][c]
                    for r, c in sats:
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < h and 0 <= cc < w:
                            out[rr][cc] = inp[r][c]
                placed_any = True
            else:
                rs = [r for r, _ in cells]
                cs = [c for _, c in cells]
                cc = (min(cs) + max(cs)) // 2
                host_col = None
                for col, positions in single_by_col.items():
                    if col == 5:
                        continue
                    if any(pc == cc and pr > max(rs) for pr, pc in positions):
                        host_col = col
                        break
                if host_col is None:
                    return None
                ar, ac = max(rs), cc
                for tr, tc in single_by_col[host_col]:
                    if (tr, tc) in killed:
                        continue
                    dr, dc = (tr - 1) - ar, tc - ac
                    for r, c in cells:
                        rr, cc_ = r + dr, c + dc
                        if 0 <= rr < h and 0 <= cc_ < w:
                            out[rr][cc_] = inp[r][c]
                    out[tr][tc] = host_col
                    placed_any = True
        if not placed_any:
            return None
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("sprite_magnet_reseat", make_sprite_magnet_reseat())]


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
            "engine": "s2_sprite_magnet_reseat",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_sprite_magnet_reseat",
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
