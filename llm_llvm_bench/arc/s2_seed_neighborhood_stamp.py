"""S2 seed neighborhood stamp (FoT).

Grammar (same_canvas_rewrite):
  Learn per-seed-color neighborhood stamps from train demos
  (relative (dr,dc) -> stamp color within Chebyshev radius 1).
  Apply stamps onto zeros only; seeds stay put.

Canonical close: AGI-2 test task 0ca9ddb6
  (color 2 → diagonal 4s; color 1 → orthogonal 7s).
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
RuleMap = Dict[int, Dict[Tuple[int, int], int]]


def _learn_rules(train: Sequence[Dict[str, Any]]) -> Optional[RuleMap]:
    rules: RuleMap = {}
    for ex in train:
        inp, out = ex["input"], ex["output"]
        if len(inp) != len(out) or (inp and len(inp[0]) != len(out[0])):
            return None
        h, w = len(inp), len(inp[0])
        seeds = [(r, c, inp[r][c]) for r in range(h) for c in range(w) if inp[r][c] != 0]
        for r, c, sc in seeds:
            for rr in range(max(0, r - 1), min(h, r + 2)):
                for cc in range(max(0, c - 1), min(w, c + 2)):
                    if (rr, cc) == (r, c):
                        continue
                    if out[rr][cc] != inp[rr][cc] and inp[rr][cc] == 0:
                        dr, dc = rr - r, cc - c
                        bucket = rules.setdefault(sc, {})
                        prev = bucket.get((dr, dc))
                        if prev is None:
                            bucket[(dr, dc)] = out[rr][cc]
                        elif prev != out[rr][cc]:
                            return None
    return rules or None


def _apply(inp: Grid, rules: RuleMap) -> Grid:
    h, w = len(inp), len(inp[0])
    out = [list(row) for row in inp]
    seeds = [(r, c, inp[r][c]) for r in range(h) for c in range(w) if inp[r][c] != 0]
    for r, c, sc in seeds:
        for (dr, dc), col in rules.get(sc, {}).items():
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and out[rr][cc] == 0:
                out[rr][cc] = col
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    rules = _learn_rules(train)
    if rules is None:
        return []

    def _xf(grid: Grid) -> Optional[Grid]:
        if not grid or not grid[0]:
            return None
        return _apply(grid, rules)

    return [("seed_neighborhood_stamp", _xf)]


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
            "engine": "s2_seed_neighborhood_stamp",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_seed_neighborhood_stamp",
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
