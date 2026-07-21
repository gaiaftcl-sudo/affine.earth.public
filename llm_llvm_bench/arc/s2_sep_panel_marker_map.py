"""S2 separator-panel marker map (FoT).

Grammar (same_canvas_rewrite):
  Grid is a 3×3 meta-array of 3×3 panels divided by solid separator
  lines of a learned separator color (rows/cols of that color).
  Exactly one panel lacks a learned marker color; the nonzero
  non-separator cells in that panel encode which meta-panels to fill
  and with which color (row/col of each seed → meta panel; value → fill).

Canonical close: AGI-2 test task 09629e4f.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

BANDS = (0, 4, 8)


def _learn_sep_marker(train: Sequence[Dict[str, Any]]) -> Optional[Tuple[int, int]]:
    sep_votes = Counter()
    marker_votes = Counter()
    for example in train:
        gi = example["input"]
        if len(gi) != 11 or any(len(r) != 11 for r in gi):
            return None
        # separator rows are fully constant
        for r in (3, 7):
            vals = set(gi[r])
            if len(vals) != 1:
                return None
            sep_votes[next(iter(vals))] += 1
        # marker = color that appears in exactly 8 of 9 panels
        panel_has: Dict[int, int] = Counter()
        colors = set()
        for br in BANDS:
            for bc in BANDS:
                cells = [gi[br + dr][bc + dc] for dr in range(3) for dc in range(3)]
                colors.update(cells)
                for col in set(cells):
                    if col != 0:
                        panel_has[col] += 1
        for col, n in panel_has.items():
            if n == 8:
                marker_votes[col] += 1
    if not sep_votes or not marker_votes:
        return None
    sep = sep_votes.most_common(1)[0][0]
    marker = marker_votes.most_common(1)[0][0]
    if sep == marker:
        return None
    return sep, marker


def _transform_with(sep: int, marker: int) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or len(inp) != 11 or any(len(r) != 11 for r in inp):
            return None
        key_panel = None
        for bi, br in enumerate(BANDS):
            for bj, bc in enumerate(BANDS):
                cells = [inp[br + dr][bc + dc] for dr in range(3) for dc in range(3)]
                if marker not in cells:
                    if key_panel is not None:
                        return None
                    key_panel = (bi, bj, br, bc)
        if key_panel is None:
            return None
        _, _, kr, kc = key_panel
        fills: Dict[Tuple[int, int], int] = {}
        for dr in range(3):
            for dc in range(3):
                v = inp[kr + dr][kc + dc]
                if v in (0, sep, marker):
                    continue
                fills[(dr, dc)] = v
        if len(fills) != 4:
            return None
        out = [[0 for _ in range(11)] for _ in range(11)]
        for c in range(11):
            out[3][c] = sep
            out[7][c] = sep
        for r in range(11):
            out[r][3] = sep
            out[r][7] = sep
        for (bi, bj), col in fills.items():
            br, bc = BANDS[bi], BANDS[bj]
            for dr in range(3):
                for dc in range(3):
                    out[br + dr][bc + dc] = col
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    learned = _learn_sep_marker(train)
    if learned is None:
        return []
    sep, marker = learned
    return [("sep_panel_marker_map", _transform_with(sep, marker))]


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
            "engine": "s2_sep_panel_marker_map",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_sep_panel_marker_map",
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
