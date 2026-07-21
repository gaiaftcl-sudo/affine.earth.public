"""S1 seed period stripe fill (FoT).

Grammar:
  Two+ nonzero seeds. If height >= width, paint full rows on a period
  lattice from the seed rows; else paint full columns from seed cols.
  Colors alternate by lattice index.

Canonical close: AGI-2 test task 0a938d79.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def seed_period_stripe_fill(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    seeds = [(r, c, inp[r][c]) for r in range(h) for c in range(w) if inp[r][c] != 0]
    if len(seeds) < 2:
        return None
    out: Grid = [[0] * w for _ in range(h)]
    if h >= w:
        seed_rows: Dict[int, int] = {}
        for r, _c, v in seeds:
            seed_rows[r] = v
        rs = sorted(seed_rows)
        if len(rs) < 2:
            return None
        period = rs[1] - rs[0]
        if period <= 0:
            return None
        for a, b in zip(rs, rs[1:]):
            if (b - a) % period != 0:
                return None
        palette = [seed_rows[r] for r in rs]
        n = len(palette)
        for r in range(h):
            if r >= rs[0] and (r - rs[0]) % period == 0:
                colr = palette[((r - rs[0]) // period) % n]
                for c in range(w):
                    out[r][c] = colr
        return out
    seed_cols: Dict[int, int] = {}
    for _r, c, v in seeds:
        seed_cols[c] = v
    cs = sorted(seed_cols)
    if len(cs) < 2:
        return None
    period = cs[1] - cs[0]
    if period <= 0:
        return None
    for a, b in zip(cs, cs[1:]):
        if (b - a) % period != 0:
            return None
    palette = [seed_cols[c] for c in cs]
    n = len(palette)
    for c in range(w):
        if c >= cs[0] and (c - cs[0]) % period == 0:
            colr = palette[((c - cs[0]) // period) % n]
            for r in range(h):
                out[r][c] = colr
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("seed_period_stripe_fill", seed_period_stripe_fill)]


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
            "engine": "s1_seed_period_stripe_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_seed_period_stripe_fill",
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
    "seed_period_stripe_fill",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
