"""S1 oriented block-pack language game (FoT).

Grammar family owned here:
  oriented_block_pack (canonical: eval task 291dc1e1)
    S1: color-0 + ones strip and color-2 + eights strip are orientation markers;
        canonicalize by D4 so markers sit on the top two rows.
    S2: remaining body splits into 2-row bands separated by full-8 rows; each
        band splits into column-blocks separated by all-8 columns.
    S3: if canonicalize used no vertical reflection (ori in {id,h}), vertically
        flip each block; canvas width = max block width; pad shorter blocks
        with 8s on both sides.
    S4: stack framed blocks top-to-bottom in band order, left-to-right.
    C4: exact packed grid; licensed only when every training pair replays.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _hflip(grid: Grid) -> Grid:
    return [list(reversed(row)) for row in grid]


def _vflip(grid: Grid) -> Grid:
    return list(reversed(grid))


def _rot90(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid[::-1])]


def _canonicalize(grid: Grid) -> Optional[Tuple[Grid, str]]:
    current = grid
    for _ in range(4):
        for name, variant in (
            ("id", current),
            ("h", _hflip(current)),
            ("v", _vflip(current)),
            ("hv", _hflip(_vflip(current))),
        ):
            if (
                len(variant) >= 3
                and len(variant[0]) >= 2
                and variant[0][0] == 0
                and all(value == 1 for value in variant[0][1:])
                and variant[1][0] == 2
                and all(value == 8 for value in variant[1][1:])
            ):
                return variant, name
        current = _rot90(current)
    return None


def oriented_block_pack(grid: Grid) -> Optional[Grid]:
    canon = _canonicalize(grid)
    if canon is None:
        return None
    oriented, name = canon
    flip_blocks = name in ("id", "h")
    body = oriented[2:]
    bands: List[Grid] = []
    current: Grid = []
    for row in body:
        if row[0] == 2 and all(value == 8 for value in row[1:]):
            if current:
                bands.append(current)
                current = []
        else:
            current.append(row)
    if current:
        bands.append(current)

    blocks: List[Grid] = []
    for band in bands:
        height = len(band)
        width = len(band[0])
        separator = [
            all(band[row][col] == 8 for row in range(height)) for col in range(width)
        ]
        separator[0] = True
        col = 0
        while col < width:
            if separator[col]:
                col += 1
                continue
            start = col
            while col < width and not separator[col]:
                col += 1
            blocks.append([row[start:col] for row in band])

    if not blocks:
        return None
    if flip_blocks:
        blocks = [block[::-1] for block in blocks]

    canvas_w = max(len(block[0]) for block in blocks)
    out: Grid = []
    for block in blocks:
        pad = canvas_w - len(block[0])
        if pad < 0:
            return None
        left = pad // 2
        right = pad - left
        out.extend([[8] * left + row + [8] * right for row in block])
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("oriented_block_pack", oriented_block_pack)]


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
            "engine": "s1_oriented_block_pack",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_oriented_block_pack",
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
    "oriented_block_pack",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
