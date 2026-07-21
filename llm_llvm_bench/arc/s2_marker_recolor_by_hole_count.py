"""S2 marker-component recolor by enclosed hole count (FoT).

Grammar (same_canvas_rewrite):
  Identify the unique nonzero marker color on the input. For each
  4-connected marker component, count zero-components enclosed by that
  component (not touching the border). Learn a stable hole-count→recolor
  map from train demos; recolor every marker cell by that map.

Canonical close: AGI-2 test task 0a2355a6.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _components(inp: Grid, color: int) -> List[List[Tuple[int, int]]]:
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    out: List[List[Tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or inp[r][c] != color:
                continue
            q = deque([(r, c)])
            seen[r][c] = True
            cells: List[Tuple[int, int]] = []
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < h and 0 <= ny < w and not seen[nx][ny] and inp[nx][ny] == color:
                        seen[nx][ny] = True
                        q.append((nx, ny))
            out.append(cells)
    return out


def _enclosed_hole_count(inp: Grid, wall_cells: Sequence[Tuple[int, int]]) -> int:
    h, w = len(inp), len(inp[0])
    wall: Set[Tuple[int, int]] = set(wall_cells)
    seen = [[False] * w for _ in range(h)]
    count = 0
    for r in range(h):
        for c in range(w):
            if seen[r][c] or inp[r][c] != 0:
                continue
            q = deque([(r, c)])
            seen[r][c] = True
            cells: List[Tuple[int, int]] = []
            border = False
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                if x in (0, h - 1) or y in (0, w - 1):
                    border = True
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < h and 0 <= ny < w):
                        border = True
                        continue
                    if (nx, ny) in wall:
                        continue
                    if inp[nx][ny] == 0 and not seen[nx][ny]:
                        seen[nx][ny] = True
                        q.append((nx, ny))
            if border:
                continue
            ok = True
            for x, y in cells:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < h and 0 <= ny < w and inp[nx][ny] != 0 and (nx, ny) not in wall:
                        ok = False
            if ok:
                count += 1
    return count


def _marker_color(train: Sequence[Dict[str, Any]]) -> Optional[int]:
    colors: Set[int] = set()
    for example in train:
        for row in example["input"]:
            colors.update(row)
    colors.discard(0)
    if len(colors) != 1:
        return None
    return next(iter(colors))


def _learn_hole_map(train: Sequence[Dict[str, Any]], marker: int) -> Optional[Dict[int, int]]:
    mapping: Dict[int, int] = {}
    for example in train:
        gi = example["input"]
        go = example["output"]
        if len(gi) != len(go) or (gi and go and len(gi[0]) != len(go[0])):
            return None
        for cells in _components(gi, marker):
            fills = {go[r][c] for r, c in cells}
            if len(fills) != 1:
                return None
            col = next(iter(fills))
            if col == 0:
                return None
            nh = _enclosed_hole_count(gi, cells)
            if nh in mapping and mapping[nh] != col:
                return None
            mapping[nh] = col
    return mapping or None


def make_recolor(marker: int, mapping: Dict[int, int]) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        out = [list(row) for row in inp]
        for cells in _components(inp, marker):
            nh = _enclosed_hole_count(inp, cells)
            col = mapping.get(nh)
            if col is None:
                return None
            for r, c in cells:
                out[r][c] = col
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    marker = _marker_color(train)
    if marker is None:
        return []
    mapping = _learn_hole_map(train, marker)
    if mapping is None:
        return []
    return [("marker_recolor_by_hole_count", make_recolor(marker, mapping))]


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
            "engine": "s2_marker_recolor_by_hole_count",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_marker_recolor_by_hole_count",
        "train_replay": f"{passed}/{len(train)}",
        "perfect": passed == len(train) and len(train) > 0,
        "passed": passed,
        "total": len(train),
        "licensed_transforms": [n for n, _ in exact],
        "primary_transform": name,
    }


def solve_task(task: Dict[str, Any]) -> Optional[List[Dict[str, Grid]]]:
    replay = train_replay(task)
    if not replay["perfect"]:
        return None
    exact = exact_candidates(task["train"])
    _, transform = exact[0]
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
