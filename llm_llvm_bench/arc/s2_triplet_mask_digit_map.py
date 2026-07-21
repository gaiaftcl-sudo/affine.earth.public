"""S2 triplet mask digit map (FoT).

Grammar (same_canvas_rewrite):
  Split a 3×9 canvas into three 3×3 masks of a marker color. Learn mask→digit
  from train; emit three solid digit blocks repeated across three rows.

Canonical close: AGI-2 test task 17cae0c1.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Mask = Tuple[int, ...]


def _mask(block: Grid, marker: int) -> Mask:
    return tuple(1 if c == marker else 0 for row in block for c in row)


def _learn(train: Sequence[Dict[str, Any]]) -> Optional[Tuple[int, Dict[Mask, int]]]:
    mapping: Dict[Mask, int] = {}
    marker = 5
    for example in train:
        gi, go = example["input"], example["output"]
        if len(gi) != 3 or len(gi[0]) != 9:
            return None
        if len(go) != 3 or len(go[0]) != 9:
            return None
        if any(row != go[0] for row in go):
            return None
        colors = [go[0][0], go[0][3], go[0][6]]
        if go[0][1] != colors[0] or go[0][2] != colors[0]:
            return None
        for gi_i, col in enumerate(colors):
            block = [gi[r][gi_i * 3 : (gi_i + 1) * 3] for r in range(3)]
            m = _mask(block, marker)
            if m in mapping and mapping[m] != col:
                return None
            mapping[m] = col
    return (marker, mapping) if mapping else None


def make_map(marker: int, mapping: Dict[Mask, int]) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or len(inp) != 3 or len(inp[0]) != 9:
            return None
        digits: List[int] = []
        for gi_i in range(3):
            block = [inp[r][gi_i * 3 : (gi_i + 1) * 3] for r in range(3)]
            m = _mask(block, marker)
            if m not in mapping:
                return None
            digits.append(mapping[m])
        row: List[int] = []
        for d in digits:
            row.extend([d, d, d])
        return [row[:], row[:], row[:]]

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    learned = _learn(train)
    if learned is None:
        return []
    marker, mapping = learned
    return [("triplet_mask_digit_map", make_map(marker, mapping))]


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
            "engine": "s2_triplet_mask_digit_map",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_triplet_mask_digit_map",
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
