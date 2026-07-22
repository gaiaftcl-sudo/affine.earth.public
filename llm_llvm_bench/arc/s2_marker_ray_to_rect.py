"""S2 marker ray to rectangle (FoT).

Grammar (same_canvas_rewrite):
  Find the largest near-solid rectangular 4-connected component. Small marker
  components that share a row-band or column-band with that rectangle paint an
  axis-aligned ray of their color toward the rectangle (exclusive of the rect
  interior). Markers off both axes are left untouched.

Canonical close: AGI-2 test task 2c608aff.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _components(inp: Grid, bg: int) -> List[Tuple[int, List[Tuple[int, int]]]]:
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    out: List[Tuple[int, List[Tuple[int, int]]]] = []
    for r in range(h):
        for c in range(w):
            if inp[r][c] == bg or seen[r][c]:
                continue
            col = inp[r][c]
            q = deque([(r, c)])
            seen[r][c] = True
            cells: List[Tuple[int, int]] = []
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and not seen[nx][ny]
                        and inp[nx][ny] == col
                    ):
                        seen[nx][ny] = True
                        q.append((nx, ny))
            out.append((col, cells))
    return out


def make_marker_ray_to_rect() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        bg = Counter(v for row in inp for v in row).most_common(1)[0][0]
        comps = _components(inp, bg)
        best = None
        for col, cells in comps:
            rs = [r for r, _ in cells]
            cs = [c for _, c in cells]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            area = (r1 - r0 + 1) * (c1 - c0 + 1)
            fill = len(cells) / area if area else 0.0
            if fill >= 0.9 and len(cells) >= 4:
                key = (len(cells), fill)
                if best is None or key > best[0]:
                    best = (key, col, (r0, r1, c0, c1))
        if best is None:
            return None
        _, rcol, (rr0, rr1, cc0, cc1) = best
        out = [list(row) for row in inp]
        painted = False
        for col, cells in comps:
            if col == rcol:
                continue
            if len(cells) > 3:
                continue
            for r, c in cells:
                if rr0 <= r <= rr1 and (c < cc0 or c > cc1):
                    if c < cc0:
                        for x in range(c + 1, cc0):
                            out[r][x] = col
                            painted = True
                    else:
                        for x in range(cc1 + 1, c):
                            out[r][x] = col
                            painted = True
                elif cc0 <= c <= cc1 and (r < rr0 or r > rr1):
                    if r < rr0:
                        for y in range(r + 1, rr0):
                            out[y][c] = col
                            painted = True
                    else:
                        for y in range(rr1 + 1, r):
                            out[y][c] = col
                            painted = True
        return out if painted else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("marker_ray_to_rect", make_marker_ray_to_rect())]


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
            "engine": "s2_marker_ray_to_rect",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_marker_ray_to_rect",
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
