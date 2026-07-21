"""S1 shape-fingerprint → singleton color (FoT).

Grammar (zoom_in_crop): map the normalized nonzero binary silhouette of the
input to a 1×1 output color learned from train demos.

Canonical close: AGI-2 test task 27a28665 (3 tests).
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Key = Tuple[Tuple[int, ...], ...]


def shape_key(inp: Grid) -> Optional[Key]:
    cells = [(r, c) for r, row in enumerate(inp) for c, v in enumerate(row) if v != 0]
    if not cells:
        return None
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    return tuple(
        tuple(1 if inp[r][c] != 0 else 0 for c in range(c0, c1 + 1))
        for r in range(r0, r1 + 1)
    )


def _learn_map(train: Sequence[Dict[str, Any]]) -> Optional[Dict[Key, int]]:
    mapping: Dict[Key, int] = {}
    for ex in train:
        out = ex["output"]
        if len(out) != 1 or len(out[0]) != 1:
            return None
        key = shape_key(ex["input"])
        if key is None:
            return None
        val = out[0][0]
        if key in mapping and mapping[key] != val:
            return None
        mapping[key] = val
    return mapping or None


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    mapping = _learn_map(train)
    if mapping is None:
        return []

    def _xf(grid: Grid) -> Optional[Grid]:
        key = shape_key(grid)
        if key is None or key not in mapping:
            return None
        return [[mapping[key]]]

    return [("shape_fingerprint_singleton", _xf)]


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
            "engine": "s1_shape_fingerprint_singleton",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_shape_fingerprint_singleton",
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
    "shape_key",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
