"""S1 odd-column slot band expand (FoT).

Grammar (zoom_out_expand):
  Marker rows (any nonzero) map to equal-height bands on a fixed 26×26 canvas.
  Odd input columns are slots; consecutive same-color slots merge into a block.
  Slot pitch is 24 / n_slots. Separator rows between bands inherit a color only
  when both adjacent bands share an identical (color, x-range) block.

Canonical close: AGI-2 test task 33067df9.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

OUT_N = 26


def oddcol_slot_band_expand(inp: Grid, bg: int = 0) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    rows = [r for r in range(h) if any(inp[r][c] != bg for c in range(w))]
    n = len(rows)
    if not rows or 24 % n:
        return None
    bh = 24 // n - 2
    n_slots = w // 2
    if n_slots <= 0 or 24 % n_slots:
        return None
    pitch = 24 // n_slots
    if bh <= 0:
        return None
    out: Grid = [[bg] * OUT_N for _ in range(OUT_N)]
    band_ranges: List[Tuple[int, int, List[Tuple[int, int, int]]]] = []
    for bi, r in enumerate(rows):
        slot_color: Dict[int, int] = {}
        for k in range(n_slots):
            c = 2 * k + 1
            if c < w and inp[r][c] != bg:
                slot_color[k] = inp[r][c]
        groups: List[List[int]] = []
        for k in sorted(slot_color):
            col = slot_color[k]
            if groups and groups[-1][0] == col and groups[-1][2] == k - 1:
                groups[-1][2] = k
            else:
                groups.append([col, k, k])
        y0 = 2 + bi * (bh + 2)
        rects: List[Tuple[int, int, int]] = []
        for col, k0, k1 in groups:
            x0 = 2 + k0 * pitch
            x1 = 2 + (k1 + 1) * pitch - 2
            rects.append((col, x0, x1))
            for dy in range(bh):
                for x in range(x0, x1):
                    out[y0 + dy][x] = col
        band_ranges.append((y0, y0 + bh, rects))
    for i in range(len(band_ranges) - 1):
        y1 = band_ranges[i][1]
        y2 = band_ranges[i + 1][0]
        for ca, xa0, xa1 in band_ranges[i][2]:
            for cb, xb0, xb1 in band_ranges[i + 1][2]:
                if ca == cb and xa0 == xb0 and xa1 == xb1:
                    for y in range(y1, y2):
                        for x in range(xa0, xa1):
                            out[y][x] = ca
    return out


def make_oddcol_slot_band_expand() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return oddcol_slot_band_expand(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("oddcol_slot_band_expand", make_oddcol_slot_band_expand())]


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
            "engine": "s1_oddcol_slot_band_expand",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_oddcol_slot_band_expand",
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
    "oddcol_slot_band_expand",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
