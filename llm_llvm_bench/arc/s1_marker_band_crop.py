"""S1 marker band crop (FoT).

Grammar (zoom_in_crop):
  Learn the marker color present in every train input (the color whose bbox
  defines the crop). Crop columns to the marker bbox; rows to [min_r-1, max_r+1]
  (clamped), capturing the marker band plus its one-cell vertical caps.

Canonical close: AGI-2 test task 3f7978a0.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _learn_marker(train: Sequence[Dict[str, Any]]) -> Optional[int]:
    # Color that appears in every train input and whose ±1 row bbox matches output.
    common: Optional[set] = None
    for example in train:
        cols = {c for row in example["input"] for c in row if c}
        common = cols if common is None else common & cols
    if not common:
        return None
    votes: Counter = Counter()
    for marker in common:
        ok = True
        for example in train:
            gi, go = example["input"], example["output"]
            cells = [
                (r, c)
                for r, row in enumerate(gi)
                for c, v in enumerate(row)
                if v == marker
            ]
            if not cells:
                ok = False
                break
            rs = [r for r, _ in cells]
            cs = [c for _, c in cells]
            h, w = len(gi), len(gi[0])
            r0 = max(0, min(rs) - 1)
            r1 = min(h - 1, max(rs) + 1)
            c0, c1 = min(cs), max(cs)
            crop = [row[c0 : c1 + 1] for row in gi[r0 : r1 + 1]]
            if crop != go:
                ok = False
                break
        if ok:
            votes[marker] += 1
    if not votes:
        return None
    return votes.most_common(1)[0][0]


def make_crop(marker: int) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        cells = [
            (r, c) for r in range(h) for c in range(w) if inp[r][c] == marker
        ]
        if not cells:
            return None
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r0 = max(0, min(rs) - 1)
        r1 = min(h - 1, max(rs) + 1)
        c0, c1 = min(cs), max(cs)
        return [row[c0 : c1 + 1] for row in inp[r0 : r1 + 1]]

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    marker = _learn_marker(train)
    if marker is None:
        return []
    return [("marker_band_crop", make_crop(marker))]


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
            "engine": "s1_marker_band_crop",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_marker_band_crop",
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
