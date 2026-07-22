"""S2 unique-band slot composite (FoT).

Grammar (zoom_in_crop):
  Grid is a 3-band stack separated by solid-8 rows; each band has a key color
  in column 0 and vertical slots separated by solid-8 columns. For each slot,
  pick the band whose normalized interior pattern is unique among the three,
  recolor its 1s to that band key, overlay 8s from the other bands, then
  concatenate slots with single-8 separators. Licensed only on perfect train replay.

Canonical close: AGI-2 test task 15660dd6.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _apply(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    row_seps = [r for r in range(h) if all(inp[r][c] == 8 for c in range(w))]
    if len(row_seps) < 2:
        return None
    bands: List[Grid] = []
    keys: List[int] = []
    prev = 0
    for s in row_seps:
        if s > prev:
            band = [row[:] for row in inp[prev:s]]
            bands.append(band)
            keys.append(band[0][0])
        prev = s + 1
    if prev < h:
        band = [row[:] for row in inp[prev:]]
        bands.append(band)
        keys.append(band[0][0])
    if len(bands) < 2:
        return None
    b0 = bands[0]
    bh, bw = len(b0), len(b0[0])
    col_seps = [c for c in range(bw) if all(b0[r][c] == 8 for r in range(bh))]
    if not col_seps:
        return None
    edges = [0] + col_seps + [bw]
    slots: List[Tuple[int, int]] = []
    for i in range(len(edges) - 1):
        c0, c1 = edges[i], edges[i + 1]
        inner = (1, c1) if i == 0 else (c0 + 1, c1)
        if inner[1] - inner[0] >= 2:
            slots.append(inner)
    if not slots:
        return None
    out_slots: List[Grid] = []
    for c0, c1 in slots:
        patterns = []
        for band, key in zip(bands, keys):
            pat = [[band[r][c] for c in range(c0, c1)] for r in range(len(band))]
            patterns.append((key, pat))
        norms = [
            tuple(tuple(1 if v == key else v for v in row) for row in pat)
            for key, pat in patterns
        ]
        chosen = None
        for i, n in enumerate(norms):
            if sum(1 for m in norms if m == n) == 1:
                chosen = i
                break
        if chosen is None:
            return None
        key, pat = patterns[chosen]
        H, W = len(pat), len(pat[0])
        out = [[key if pat[r][c] == 1 else pat[r][c] for c in range(W)] for r in range(H)]
        for j, (_, p2) in enumerate(patterns):
            if j == chosen:
                continue
            for r in range(H):
                for c in range(W):
                    if p2[r][c] == 8:
                        out[r][c] = 8
        out_slots.append(out)
    H = len(out_slots[0])
    rows: Grid = []
    for r in range(H):
        row: List[int] = []
        for i, sl in enumerate(out_slots):
            if i:
                row.append(8)
            row.extend(sl[r])
        rows.append(row)
    return rows


def make_unique_band_slot_composite() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _apply(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("unique_band_slot_composite", make_unique_band_slot_composite())]


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
            "engine": "s2_unique_band_slot_composite",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_unique_band_slot_composite",
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
