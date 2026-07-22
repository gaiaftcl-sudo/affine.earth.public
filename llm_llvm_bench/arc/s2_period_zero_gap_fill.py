"""S2 period zero-gap fill (FoT).

Grammar (same_canvas_rewrite):
  Infer a horizontal period on each row from nonzero cells; fill zeros by that
  residue palette. Any remaining zeros are filled the same way by column period.
  Licensed only on perfect train replay.

Canonical close: AGI-2 test task 1d0a4b61.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _best_period(vals: Sequence[int]) -> Optional[int]:
    n = len(vals)
    if 0 not in vals:
        return None
    best: Optional[Tuple[int, int]] = None
    for p in range(1, n // 2 + 1):
        ok = True
        hits = 0
        for i, v in enumerate(vals):
            if v == 0:
                continue
            for j in range(i % p, n, p):
                if vals[j] != 0 and vals[j] != v:
                    ok = False
                    break
                if vals[j] == v:
                    hits += 1
            if not ok:
                break
        if ok and hits > 0:
            if best is None or hits > best[0] or (hits == best[0] and p < best[1]):
                best = (hits, p)
    return None if best is None else best[1]


def _fill_line(vals: List[int]) -> Optional[List[int]]:
    p = _best_period(vals)
    if p is None:
        return None
    pal: List[Optional[int]] = [None] * p
    for i, v in enumerate(vals):
        if v != 0:
            pal[i % p] = v
    if any(x is None for x in pal):
        return None
    out = list(vals)
    for i, v in enumerate(out):
        if v == 0:
            out[i] = int(pal[i % p])  # type: ignore[arg-type]
    return out


def make_period_zero_gap_fill() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        if not any(v == 0 for row in inp for v in row):
            return None
        out = [row[:] for row in inp]
        changed = False
        for r in range(h):
            filled = _fill_line(out[r])
            if filled is None:
                continue
            if filled != out[r]:
                changed = True
            out[r] = filled
        if any(out[r][c] == 0 for r in range(h) for c in range(w)):
            for c in range(w):
                col = [out[r][c] for r in range(h)]
                filled = _fill_line(col)
                if filled is None:
                    continue
                for r in range(h):
                    if out[r][c] != filled[r]:
                        changed = True
                    out[r][c] = filled[r]
        if any(out[r][c] == 0 for r in range(h) for c in range(w)):
            return None
        return out if changed else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("period_zero_gap_fill", make_period_zero_gap_fill())]


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
            "engine": "s2_period_zero_gap_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_period_zero_gap_fill",
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
