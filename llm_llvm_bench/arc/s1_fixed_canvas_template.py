"""S1 fixed-canvas template crop language game (FoT).

Grammar family owned here:
  fixed_canvas_template_crop (canonical: eval task 269e22fb)
    S1: output canvas is always 20×20 (≠ variable input size).
    S2: exactly two colors; every train/test output is one dihedral of a single
        binary template (optionally bit-inverted), recolored to the input pair.
    S3: input is an exact crop of that oriented template under a 2-color bit map.
    C4: emit the full oriented 20×20; licensed only when every train pair replays.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

CANVAS = 20


def _rot90(grid: Grid) -> Grid:
    height, width = len(grid), len(grid[0])
    return [[grid[height - 1 - row][col] for row in range(height)] for col in range(width)]


def _hflip(grid: Grid) -> Grid:
    return [list(reversed(row)) for row in grid]


def _dihedral(grid: Grid) -> List[Grid]:
    out: List[Grid] = []
    seen: List[Grid] = []
    current = grid
    for _ in range(4):
        for variant in (current, _hflip(current)):
            if variant not in seen:
                seen.append(variant)
                out.append(variant)
        current = _rot90(current)
    return out


def _to_binary(grid: Grid) -> Tuple[Grid, int, int]:
    counts = Counter(value for row in grid for value in row)
    if len(counts) != 2:
        raise ValueError("expected exactly two colors")
    majority = max(counts, key=counts.get)
    minority = next(color for color in counts if color != majority)
    binary = [[1 if value == majority else 0 for value in row] for row in grid]
    return binary, majority, minority


def _invert(binary: Grid) -> Grid:
    return [[1 - bit for bit in row] for row in binary]


def _crop(grid: Grid, row0: int, col0: int, height: int, width: int) -> Grid:
    return [row[col0 : col0 + width] for row in grid[row0 : row0 + height]]


def _recolor(binary: Grid, color0: int, color1: int) -> Grid:
    return [[color1 if bit else color0 for bit in row] for row in binary]


def _template_variants(template: Grid) -> List[Grid]:
    variants: List[Grid] = []
    for oriented in _dihedral(template):
        for candidate in (oriented, _invert(oriented)):
            if candidate not in variants:
                variants.append(candidate)
    return variants


def _match_crop(
    grid: Grid, variants: Sequence[Grid]
) -> Optional[Tuple[Grid, int, int]]:
    height, width = len(grid), len(grid[0])
    colors = sorted({value for row in grid for value in row})
    if len(colors) != 2:
        return None
    for color0, color1 in ((colors[0], colors[1]), (colors[1], colors[0])):
        binary_in = [[0 if value == color0 else 1 for value in row] for row in grid]
        for variant in variants:
            if len(variant) != CANVAS or len(variant[0]) != CANVAS:
                continue
            for row0 in range(CANVAS - height + 1):
                for col0 in range(CANVAS - width + 1):
                    if _crop(variant, row0, col0, height, width) == binary_in:
                        return variant, color0, color1
    return None


def _extract_template(train: Sequence[Dict[str, Any]]) -> Optional[Grid]:
    if not train:
        return None
    try:
        template, _, _ = _to_binary(train[0]["output"])
    except ValueError:
        return None
    if len(template) != CANVAS or len(template[0]) != CANVAS:
        return None
    variants = _template_variants(template)
    for example in train:
        matched = _match_crop(example["input"], variants)
        if matched is None:
            return None
        variant, color0, color1 = matched
        if _recolor(variant, color0, color1) != example["output"]:
            return None
    return template


def make_transform(template: Grid) -> Transform:
    variants = _template_variants(template)

    def transform(grid: Grid) -> Optional[Grid]:
        matched = _match_crop(grid, variants)
        if matched is None:
            return None
        variant, color0, color1 = matched
        return _recolor(variant, color0, color1)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    template = _extract_template(train)
    if template is None:
        return []
    return [("fixed_canvas_template_crop", make_transform(template))]


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
            "engine": "s1_fixed_canvas_template",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_fixed_canvas_template",
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
    "make_transform",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
