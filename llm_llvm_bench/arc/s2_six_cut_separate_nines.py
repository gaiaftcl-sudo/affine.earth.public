"""S2 six-cut separate nines (FoT).

Grammar (same_canvas_rewrite):
  Color 6 cells are cuts. Treat 9-cells as pieces split by those cuts (6s are
  not 9-connected). For each 4-connected 9-piece, move it one step away from
  the centroid of its adjacent cuts along the dominant axis (row if
  |Δr| ≥ |Δc|, else column). Cuts disappear (become 0).

Canonical close: AGI-2 test task 2faf500b.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]


def _comps9(mask: List[List[bool]]) -> List[List[Cell]]:
    h, w = len(mask), len(mask[0])
    seen = [[False] * w for _ in range(h)]
    out: List[List[Cell]] = []
    for r in range(h):
        for c in range(w):
            if not mask[r][c] or seen[r][c]:
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
                        and mask[nx][ny]
                    ):
                        seen[nx][ny] = True
                        q.append((nx, ny))
            out.append(cells)
    return out


def make_six_cut_separate_nines(
    fill: int = 9, cut: int = 6, bg: int = 0
) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        cuts = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == cut]
        if not cuts:
            return None
        if not any(inp[r][c] == fill for r in range(h) for c in range(w)):
            return None
        mask = [[inp[r][c] == fill for c in range(w)] for r in range(h)]
        pieces = _comps9(mask)
        if not pieces:
            return None
        out = [[bg] * w for _ in range(h)]
        for cells in pieces:
            pr = sum(r for r, _ in cells) / len(cells)
            pc = sum(c for _, c in cells) / len(cells)
            adj = [
                q
                for q in cuts
                if any(abs(q[0] - r) + abs(q[1] - c) == 1 for r, c in cells)
            ]
            use = (
                adj
                if adj
                else [min(cuts, key=lambda q: abs(q[0] - pr) + abs(q[1] - pc))]
            )
            cr = sum(q[0] for q in use) / len(use)
            cc = sum(q[1] for q in use) / len(use)
            dr = 0 if abs(pr - cr) < 1e-9 else (1 if pr > cr else -1)
            dc = 0 if abs(pc - cc) < 1e-9 else (1 if pc > cc else -1)
            if abs(pr - cr) >= abs(pc - cc):
                dc = 0
            else:
                dr = 0
            for r, c in cells:
                rr, cc_ = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc_ < w:
                    out[rr][cc_] = fill
                else:
                    out[r][c] = fill
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("six_cut_separate_nines", make_six_cut_separate_nines())]


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
            "engine": "s2_six_cut_separate_nines",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, _ = exact[0]
    passed = len(train)
    return {
        "engine": "s2_six_cut_separate_nines",
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
