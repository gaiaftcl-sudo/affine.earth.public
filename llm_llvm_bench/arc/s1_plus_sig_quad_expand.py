"""S1 plus-signature quad expand (FoT).

Grammar: zoom_out_expand on a 5×5 plus-motif (corner / plus / ring roles).
Output is 10×10:

  [ input | row-broadcast(sig) ]
  [ col-broadcast(sig) | BR(role template) ]

where sig = [corner, plus, ring, corner, plus].

Canonical close: AGI-2 test task 3979b1a8.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

# BR role template (C=corner, P=plus, R=ring), learned from demos.
_BR_TMPL = (
    "PPRCP",
    "PRRCP",
    "RRCCP",
    "CCCPP",
    "PPPPR",
)


def _roles(inp: Grid) -> Optional[Tuple[int, int, int]]:
    if len(inp) != 5 or any(len(row) != 5 for row in inp):
        return None
    corner = inp[0][0]
    plus = inp[2][2]
    ring = inp[0][1]
    if corner == plus or plus == ring or corner == ring:
        return None
    # Corners must agree; plus-cross center color must be plus.
    for r, c in ((0, 0), (0, 4), (4, 0), (4, 4)):
        if inp[r][c] != corner:
            return None
    if inp[2][2] != plus:
        return None
    return corner, plus, ring


def plus_sig_quad_expand(inp: Grid) -> Optional[Grid]:
    roles = _roles(inp)
    if roles is None:
        return None
    corner, plus, ring = roles
    role = {"C": corner, "P": plus, "R": ring}
    sig = [corner, plus, ring, corner, plus]
    n = 5
    out: Grid = [[0] * (2 * n) for _ in range(2 * n)]
    for r in range(n):
        for c in range(n):
            out[r][c] = inp[r][c]
            out[r][n + c] = sig[c]
            out[n + r][c] = sig[r]
            out[n + r][n + c] = role[_BR_TMPL[r][c]]
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    if not train:
        return []
    for ex in train:
        if _roles(ex["input"]) is None:
            return []

    def _xf(grid: Grid) -> Optional[Grid]:
        return plus_sig_quad_expand(grid)

    return [("plus_sig_quad_expand_5", _xf)]


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
            "engine": "s1_plus_sig_quad_expand",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_plus_sig_quad_expand",
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
    "plus_sig_quad_expand",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
