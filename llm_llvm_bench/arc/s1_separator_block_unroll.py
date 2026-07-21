"""S1 separator-block unroll language game (FoT).

Grammar family owned here:
  separator_block_unroll (canonical: eval task 78332cb0)
    S1: separator color forms full rows/cols partitioning equal rectangular blocks.
    S2: 1D vertical stack → swap first/last block; odd count → horizontal pack,
        even count → vertical pack. 1D horizontal stack → keep order; odd →
        vertical pack, even → horizontal pack.
    S3: 2D grid → main-diagonal then off-diagonal reading order. If >1 motif
        colors (non-border, non-sep) → vertical pack; else swap ends + horizontal.
    S4: packs re-insert separator lines between blocks.
    C4: exact unroll licensed by full train replay.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _segments(seps: List[int], n: int) -> List[Tuple[int, int]]:
    edges = [-1] + seps + [n]
    out: List[Tuple[int, int]] = []
    for i in range(len(edges) - 1):
        start, end = edges[i] + 1, edges[i + 1] - 1
        if start <= end:
            out.append((start, end))
    return out


def _stack_vertical(blocks: Sequence[Grid], sep: int) -> Grid:
    width = len(blocks[0][0])
    out: Grid = []
    for index, block in enumerate(blocks):
        if index:
            out.append([sep] * width)
        out.extend([list(row) for row in block])
    return out


def _stack_horizontal(blocks: Sequence[Grid], sep: int) -> Grid:
    height = len(blocks[0])
    out: Grid = [[] for _ in range(height)]
    for index, block in enumerate(blocks):
        if index:
            for row in range(height):
                out[row].append(sep)
        for row in range(height):
            out[row].extend(block[row])
    return out


def _swap_ends(blocks: Sequence[Grid]) -> List[Grid]:
    if len(blocks) < 2:
        return [list(map(list, block)) for block in blocks]
    out = [list(map(list, block)) for block in blocks]
    out[0], out[-1] = out[-1], out[0]
    return out


def _find_separator(grid: Grid) -> Optional[Tuple[int, List[int], List[int], List[Tuple[int, int]], List[Tuple[int, int]]]]:
    height, width = len(grid), len(grid[0])
    best: Optional[Tuple[Tuple[int, int, int], int, List[int], List[int], List[Tuple[int, int]], List[Tuple[int, int]]]] = None
    for sep in range(10):
        sep_rows = [r for r in range(height) if all(value == sep for value in grid[r])]
        sep_cols = [
            c for c in range(width) if all(grid[r][c] == sep for r in range(height))
        ]
        if not sep_rows and not sep_cols:
            continue
        if sep_rows and not sep_cols:
            row_segs = _segments(sep_rows, height)
            heights = [end - start + 1 for start, end in row_segs]
            if len(row_segs) < 2 or len(set(heights)) != 1:
                continue
            score = (len(row_segs), 0, -sep)
            cand = (score, sep, sep_rows, sep_cols, row_segs, [(0, width - 1)])
        elif sep_cols and not sep_rows:
            col_segs = _segments(sep_cols, width)
            widths = [end - start + 1 for start, end in col_segs]
            if len(col_segs) < 2 or len(set(widths)) != 1:
                continue
            score = (len(col_segs), 0, -sep)
            cand = (score, sep, sep_rows, sep_cols, [(0, height - 1)], col_segs)
        else:
            row_segs = _segments(sep_rows, height)
            col_segs = _segments(sep_cols, width)
            heights = [end - start + 1 for start, end in row_segs]
            widths = [end - start + 1 for start, end in col_segs]
            if (
                len(row_segs) < 2
                or len(col_segs) < 2
                or len(set(heights)) != 1
                or len(set(widths)) != 1
            ):
                continue
            score = (len(row_segs) * len(col_segs), 1, -sep)
            cand = (score, sep, sep_rows, sep_cols, row_segs, col_segs)
        if best is None or cand[0] > best[0]:
            best = cand
    if best is None:
        return None
    _, sep, sep_rows, sep_cols, row_segs, col_segs = best
    return sep, sep_rows, sep_cols, row_segs, col_segs


def separator_block_unroll(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    found = _find_separator(grid)
    if found is None:
        return None
    sep, sep_rows, sep_cols, row_segs, col_segs = found

    if sep_rows and sep_cols:
        block_grid = [
            [
                [list(row[c0 : c1 + 1]) for row in grid[r0 : r1 + 1]]
                for c0, c1 in col_segs
            ]
            for r0, r1 in row_segs
        ]
        rows, cols = len(block_grid), len(block_grid[0])
        ordered: List[Grid] = []
        for index in range(min(rows, cols)):
            ordered.append(block_grid[index][index])
        for row in range(rows):
            for col in range(cols):
                if row != col:
                    ordered.append(block_grid[row][col])
        border = Counter(value for row in ordered[0] for value in row).most_common(1)[0][0]
        motifs = {
            value
            for block in ordered
            for row in block
            for value in row
            if value != sep and value != border
        }
        if len(motifs) > 1:
            return _stack_vertical(ordered, sep)
        return _stack_horizontal(_swap_ends(ordered), sep)

    if sep_rows and not sep_cols:
        blocks = [[list(row) for row in grid[start : end + 1]] for start, end in row_segs]
        blocks = _swap_ends(blocks)
        if len(blocks) % 2 == 1:
            return _stack_horizontal(blocks, sep)
        return _stack_vertical(blocks, sep)

    if sep_cols and not sep_rows:
        blocks = [
            [row[start : end + 1] for row in grid] for start, end in col_segs
        ]
        if len(blocks) % 2 == 1:
            return _stack_vertical(blocks, sep)
        return _stack_horizontal(blocks, sep)
    return None


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("separator_block_unroll", separator_block_unroll)]


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
            "engine": "s1_separator_block_unroll",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_separator_block_unroll",
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
    "separator_block_unroll",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
