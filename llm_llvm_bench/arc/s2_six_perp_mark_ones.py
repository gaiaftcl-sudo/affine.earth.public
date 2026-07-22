"""S2 six-perp mark ones (FoT).

Grammar (same_canvas_rewrite):
  Pair each color-6 cell with the nearest unused color-1 cell (Manhattan).
  Clear the 6 to 8. Place a 7 at the 1 plus a 90° CCW rotation of the vector
  from that 1 to the 6: if v = (dr, dc) then mark at (tr - dc, tc + dr).

Canonical close: AGI-2 test task 1a244afd.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]


def make_six_perp_mark_ones(
    six: int = 6, one: int = 1, clear: int = 8, mark: int = 7
) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        sixes = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == six]
        ones = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == one]
        if not sixes or not ones:
            return None
        out = [list(row) for row in inp]
        used: set[Cell] = set()
        placed = False
        for sr, sc in sixes:
            best: Optional[Cell] = None
            best_d = 10**9
            for tr, tc in ones:
                if (tr, tc) in used:
                    continue
                d = abs(sr - tr) + abs(sc - tc)
                if d < best_d:
                    best_d = d
                    best = (tr, tc)
            if best is None:
                continue
            tr, tc = best
            used.add(best)
            dr, dc = sr - tr, sc - tc
            pr, pc = tr - dc, tc + dr
            out[sr][sc] = clear
            if 0 <= pr < h and 0 <= pc < w:
                out[pr][pc] = mark
                placed = True
        if not placed:
            return None
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("six_perp_mark_ones", make_six_perp_mark_ones())]


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
            "engine": "s2_six_perp_mark_ones",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, _ = exact[0]
    passed = len(train)
    return {
        "engine": "s2_six_perp_mark_ones",
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
