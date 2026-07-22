"""S2 sep-6 legend stamp-3 (FoT).

Grammar (zoom_in_crop / same_canvas on bottom panel):
  A solid row of 6 separates top legend from bottom program. Top holds three
  3x3 color blocks A,B,C (left-to-right) and a control row of markers under
  them; each marker value maps to its column's block color. On a 7-canvas the
  size of the bottom panel, each non-7 bottom cell at (r,c) stamps a 3x3 of
  map[value] with top-left at (r-1,c-1). Licensed only on perfect train replay.

Canonical close: AGI-2 test task 20fb2937.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _apply(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    sep = None
    for r, row in enumerate(inp):
        if len(set(row)) == 1 and row[0] == 6:
            sep = r
            break
    if sep is None or sep < 5 or sep + 1 >= h:
        return None
    top = inp[:sep]
    bot = inp[sep + 1 :]
    bh = len(bot)
    if bh < 1:
        return None
    # three 3x3 block colors on row 0
    row0 = top[0]
    blocks: List[Tuple[int, int]] = []  # (color, start_col)
    c = 0
    while c < w:
        if row0[c] != 7:
            c0 = c
            col = row0[c]
            while c < w and row0[c] == col:
                c += 1
            if c - c0 == 3 and all(
                top[r][cc] == col for r in range(min(3, len(top))) for cc in range(c0, c)
            ):
                blocks.append((col, c0))
        else:
            c += 1
    if len(blocks) != 3:
        return None
    # control row: first row in top after the 3x3 block rows that is not all 7
    # and contains markers (values not in block colors or 7)
    block_cols = {b[0] for b in blocks}
    ctrl = None
    for r in range(3, len(top)):
        if all(v == 7 for v in top[r]):
            continue
        marks = [(c, top[r][c]) for c in range(w) if top[r][c] not in block_cols | {7}]
        if len(marks) >= 3:
            ctrl = top[r]
            break
    if ctrl is None:
        return None
    mapping: Dict[int, int] = {}
    for color, c0 in blocks:
        # marker in control under this block (cols c0..c0+2), prefer center
        found = None
        for cc in (c0 + 1, c0, c0 + 2):
            v = ctrl[cc]
            if v not in block_cols | {7}:
                found = v
                break
        if found is None:
            return None
        mapping[found] = color
    if len(mapping) != 3:
        return None

    out = [[7] * w for _ in range(bh)]
    stamped = False
    for r in range(bh):
        for c in range(w):
            v = bot[r][c]
            if v == 7:
                continue
            if v not in mapping:
                return None
            col = mapping[v]
            r0, c0 = r - 1, c - 1
            if r0 < 0 or c0 < 0 or r0 + 2 >= bh or c0 + 2 >= w:
                return None
            for dr in range(3):
                for dc in range(3):
                    out[r0 + dr][c0 + dc] = col
            stamped = True
    return out if stamped else None


def make_sep6_legend_stamp3() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _apply(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("sep6_legend_stamp3", make_sep6_legend_stamp3())]


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
            "engine": "s2_sep6_legend_stamp3",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_sep6_legend_stamp3",
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
