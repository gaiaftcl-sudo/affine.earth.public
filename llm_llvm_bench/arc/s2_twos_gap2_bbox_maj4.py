"""S2 twos gap-2 bbox majority→4 (FoT).

Grammar (same_canvas_rewrite):
  Color-2 cells stay. Merge 8-connected 2-components whose cells are within
  Chebyshev distance ≤ 2. For each merged group, take the axis-aligned bbox
  and recolor every majority non-bg/non-2 cell inside that bbox to 4.

Canonical close: AGI-2 test task 36fdfd69.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]


def _comps8(inp: Grid, color: int) -> List[List[Cell]]:
    h, w = len(inp), len(inp[0])
    seen: set[Cell] = set()
    out: List[List[Cell]] = []
    for r in range(h):
        for c in range(w):
            if inp[r][c] != color or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells: List[Cell] = []
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nx, ny = x + dr, y + dc
                        if (
                            0 <= nx < h
                            and 0 <= ny < w
                            and inp[nx][ny] == color
                            and (nx, ny) not in seen
                        ):
                            seen.add((nx, ny))
                            q.append((nx, ny))
            out.append(cells)
    return out


def _merge_gap2(comps: List[List[Cell]], gap: int = 2) -> List[List[Cell]]:
    n = len(comps)
    if n == 0:
        return []
    parent = list(range(n))

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(n):
        for j in range(i + 1, n):
            linked = False
            for r1, c1 in comps[i]:
                for r2, c2 in comps[j]:
                    if max(abs(r1 - r2), abs(c1 - c2)) <= gap:
                        linked = True
                        break
                if linked:
                    break
            if linked:
                union(i, j)
    groups: Dict[int, List[Cell]] = {}
    for i, comp in enumerate(comps):
        groups.setdefault(find(i), []).extend(comp)
    return list(groups.values())


def make_twos_gap2_bbox_maj4(marker: int = 2, paint: int = 4, bg: int = 0) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        cnt = Counter(v for row in inp for v in row if v not in (bg, marker))
        if not cnt:
            return None
        maj = cnt.most_common(1)[0][0]
        groups = _merge_gap2(_comps8(inp, marker), gap=2)
        if not groups:
            return None
        out = [row[:] for row in inp]
        changed = False
        for cells in groups:
            rs = [r for r, _ in cells]
            cs = [c for _, c in cells]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if inp[r][c] == maj:
                        out[r][c] = paint
                        changed = True
        return out if changed else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("twos_gap2_bbox_maj4", make_twos_gap2_bbox_maj4())]


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
            "engine": "s2_twos_gap2_bbox_maj4",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_twos_gap2_bbox_maj4",
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
