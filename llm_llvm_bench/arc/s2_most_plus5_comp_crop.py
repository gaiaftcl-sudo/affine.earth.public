"""S2 most size-5 marker-comp crop (FoT).

Grammar (zoom_in_crop):
  Nonzero cells form filled components of colors {marker=3, field=8} on zero
  background. Within each component, count 4-connected marker blobs of size
  exactly 5. Crop the bounding box of the component with the most such blobs
  (tie-break: larger component). Licensed only on perfect train replay.

Canonical close: AGI-2 test task 2c0b0aff.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_N4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_MARKER = 3
_BLOB = 5


def _crop_most_plus5(inp: Grid, marker: int = _MARKER, blob: int = _BLOB) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    seen = [[False] * w for _ in range(h)]
    best: Optional[Tuple[int, int, int, int, int, int]] = None
    for r in range(h):
        for c in range(w):
            if inp[r][c] == 0 or seen[r][c]:
                continue
            q = deque([(r, c)])
            seen[r][c] = True
            cells: List[Tuple[int, int]] = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in _N4:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and inp[nr][nc] != 0:
                        seen[nr][nc] = True
                        q.append((nr, nc))
            tcells = [(rr, cc) for rr, cc in cells if inp[rr][cc] == marker]
            tset = set(tcells)
            tseen = set()
            n5 = 0
            for cell in tcells:
                if cell in tseen:
                    continue
                qq = deque([cell])
                tseen.add(cell)
                n = 0
                while qq:
                    rr, cc = qq.popleft()
                    n += 1
                    for dr, dc in _N4:
                        nr, nc = rr + dr, cc + dc
                        if (nr, nc) in tset and (nr, nc) not in tseen:
                            tseen.add((nr, nc))
                            qq.append((nr, nc))
                if n == blob:
                    n5 += 1
            rs = [rr for rr, _ in cells]
            cs = [cc for _, cc in cells]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            cand = (n5, len(cells), r0, c0, r1, c1)
            if best is None or cand[:2] > best[:2]:
                best = cand
    if best is None:
        return None
    _, _, r0, c0, r1, c1 = best
    return [row[c0 : c1 + 1] for row in inp[r0 : r1 + 1]]


def make_most_plus5_comp_crop() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _crop_most_plus5(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("most_plus5_comp_crop", make_most_plus5_comp_crop())]


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
            "engine": "s2_most_plus5_comp_crop",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_most_plus5_comp_crop",
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
