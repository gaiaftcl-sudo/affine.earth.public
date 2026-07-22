"""S1 triplet vertical-panel growth extrapolate (FoT).

Grammar (zoom_in_crop): input is three equal-height row panels stacked.
Learn the cellwise growth from panel0 → panel1 (a value that appears by
extending a same-colored neighbor in panel0 continues one step further).
Apply that wavefront once more onto panel1 to produce the next frame.

Canonical close: AGI-2 test task 2ccd9fef.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _vthirds(inp: Grid) -> Optional[Tuple[Grid, Grid, Grid]]:
    h = len(inp)
    if h % 3 != 0:
        return None
    k = h // 3
    return inp[:k], inp[k : 2 * k], inp[2 * k :]


def _hthirds(inp: Grid) -> Optional[Tuple[Grid, Grid, Grid]]:
    w = len(inp[0])
    if w % 3 != 0:
        return None
    k = w // 3
    return (
        [row[:k] for row in inp],
        [row[k : 2 * k] for row in inp],
        [row[2 * k :] for row in inp],
    )


def _panel_pair_score(p0: Grid, p1: Grid) -> int:
    """Higher when borders match — same frame family."""
    h, w = len(p0), len(p0[0])
    score = 0
    for c in range(w):
        if p0[0][c] == p1[0][c]:
            score += 1
        if p0[h - 1][c] == p1[h - 1][c]:
            score += 1
    for r in range(h):
        if p0[r][0] == p1[r][0]:
            score += 1
        if p0[r][w - 1] == p1[r][w - 1]:
            score += 1
    return score


def extrapolate_growth(p0: Grid, p1: Grid) -> Optional[Grid]:
    if not p0 or not p1 or len(p0) != len(p1) or len(p0[0]) != len(p1[0]):
        return None
    h, w = len(p0), len(p0[0])
    out: Grid = [list(row) for row in p1]
    for r in range(h):
        for c in range(w):
            if p0[r][c] == p1[r][c]:
                continue
            v = p1[r][c]
            if c > 0 and p0[r][c - 1] == v and c + 1 < w:
                out[r][c + 1] = v
            if c + 1 < w and p0[r][c + 1] == v and c - 1 >= 0:
                out[r][c - 1] = v
            if r > 0 and p0[r - 1][c] == v and r + 1 < h:
                out[r + 1][c] = v
            if r + 1 < h and p0[r + 1][c] == v and r - 1 >= 0:
                out[r - 1][c] = v
    return out


def _candidate_splits(inp: Grid) -> List[Tuple[Grid, Grid, Grid]]:
    out: List[Tuple[Grid, Grid, Grid]] = []
    vt = _vthirds(inp)
    if vt is not None:
        out.append(vt)
    ht = _hthirds(inp)
    if ht is not None:
        out.append(ht)
    h, w = len(inp), len(inp[0])
    rem = w % 3
    if rem and w > rem:
        cropped = [row[: w - rem] for row in inp]
        ht2 = _hthirds(cropped)
        if ht2 is not None:
            out.append(ht2)
        cropped = [row[rem:] for row in inp]
        ht3 = _hthirds(cropped)
        if ht3 is not None:
            out.append(ht3)
    remh = h % 3
    if remh and h > remh:
        vt2 = _vthirds(inp[: h - remh])
        if vt2 is not None:
            out.append(vt2)
        vt3 = _vthirds(inp[remh:])
        if vt3 is not None:
            out.append(vt3)
    return out


def triplet_grow(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    splits = _candidate_splits(inp)
    if not splits:
        return None
    # Prefer vertical when height divides (train geometry); else best border score.
    h = len(inp)
    if h % 3 == 0:
        parts = _vthirds(inp)
        if parts is not None:
            return extrapolate_growth(parts[0], parts[1])
    best: Optional[Grid] = None
    best_score = -1
    for p0, p1, _p2 in splits:
        score = _panel_pair_score(p0, p1)
        pred = extrapolate_growth(p0, p1)
        if pred is None:
            continue
        if score > best_score:
            best_score = score
            best = pred
    return best


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    if not train:
        return []
    # Train demos are vertical thirds (h % 3 == 0).
    if not all(
        (lambda p: p is not None and extrapolate_growth(p[0], p[1]) == ex["output"])(
            _vthirds(ex["input"])
        )
        for ex in train
    ):
        return []

    def _xf(grid: Grid) -> Optional[Grid]:
        return triplet_grow(grid)

    return [("triplet_panel_grow_extrapolate", _xf)]


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
            "engine": "s1_triplet_panel_grow_extrapolate",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_triplet_panel_grow_extrapolate",
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
    "extrapolate_growth",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
    "triplet_grow",
]
