"""S1 digit-separator snake pack (FoT).

Grammar family owned here:
  digit_separator_snake (canonical: eval task 136b0064)
    S1: output width shrinks (drop separator + right marker strip → 7 cols).
    S2: left of sep = stacked 3×7 panels of two 3×3 digit glyphs; right = marker 5.
    S3: read left-column digits top→bottom, then right-column digits; emit snake.
    S4: each glyph attaches to previous via a typed port (1→right; 2/3/6→left/sole);
        next glyph seats a typed cell on that port (1/6 left/sole; 2/3 right).
    C4: exact 7-wide canvas with marker row preserved; train-replay gated.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

WIDTH = {1: 3, 2: 2, 3: 4, 6: 1}
HEIGHT = {1: 1, 2: 1, 3: 1, 6: 2}
SHAPES = {
    1: [(0, 0), (0, 1), (0, 2)],
    2: [(0, 0), (0, 1)],
    3: [(0, 0), (0, 1), (0, 2), (0, 3)],
    6: [(0, 0), (1, 0)],
}


def _extract_panels(left: Grid) -> List[Grid]:
    height = len(left)
    panels: List[Grid] = []
    row = 0
    while row < height:
        if all(value == 0 for value in left[row]):
            row += 1
            continue
        block: Grid = []
        while row < height and any(value != 0 for value in left[row]):
            block.append(left[row])
            row += 1
        if block:
            panels.append(block)
    return panels


def _digit_color(crop: Grid) -> Optional[int]:
    for row in crop:
        for value in row:
            if value != 0:
                return value
    return None


def digit_sequence(grid: Grid) -> Optional[Tuple[List[int], int, int]]:
    """Return (Ls+Rs digit colors, marker_row, marker_col) or None."""
    if not grid or not grid[0] or len(grid[0]) != 15:
        return None
    left = [row[:7] for row in grid]
    right = [row[8:] for row in grid]
    marker = [
        (r, c)
        for r, row in enumerate(right)
        for c, value in enumerate(row)
        if value == 5
    ]
    if len(marker) != 1:
        return None
    marker_row, marker_col = marker[0]
    lefts: List[int] = []
    rights: List[int] = []
    for panel in _extract_panels(left):
        if not panel or any(len(row) != 7 for row in panel):
            return None
        left_crop = [[row[c] for c in range(3)] for row in panel]
        right_crop = [[row[c] for c in range(4, 7)] for row in panel]
        left_color = _digit_color(left_crop)
        right_color = _digit_color(right_crop)
        if left_color not in WIDTH or right_color not in WIDTH:
            return None
        lefts.append(left_color)
        rights.append(right_color)
    if not lefts:
        return None
    return lefts + rights, marker_row, marker_col


def _port(prev_digit: int, prev_anc: int) -> int:
    if prev_digit == 1:
        return prev_anc + WIDTH[1] - 1
    return prev_anc


def _place_on_port(next_digit: int, port_col: int) -> int:
    if next_digit in (1, 6):
        return port_col
    return port_col - (WIDTH[next_digit] - 1)


def digit_separator_snake(grid: Grid) -> Optional[Grid]:
    parsed = digit_sequence(grid)
    if parsed is None:
        return None
    seq, marker_row, marker_col = parsed
    height = len(grid)
    width = 7
    out = [[0] * width for _ in range(height)]
    out[marker_row][marker_col] = 5
    anchors = [_place_on_port(seq[0], marker_col)]
    for index in range(1, len(seq)):
        anchors.append(
            _place_on_port(seq[index], _port(seq[index - 1], anchors[-1]))
        )
    row = marker_row + 1
    for digit, anc in zip(seq, anchors):
        if anc < 0 or anc + WIDTH[digit] > width:
            return None
        if row + HEIGHT[digit] > height:
            return None
        for dr, dc in SHAPES[digit]:
            out[row + dr][anc + dc] = digit
        row += HEIGHT[digit]
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("digit_separator_snake", digit_separator_snake)]


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
            "engine": "s1_digit_separator_snake",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_digit_separator_snake",
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
        attempts.append(
            {"attempt_1": pred, "attempt_2": [list(row) for row in pred]}
        )
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
    "digit_separator_snake",
    "digit_sequence",
    "exact_candidates",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
