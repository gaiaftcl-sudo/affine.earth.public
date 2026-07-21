"""S2 seven-triplet rail palette rewrite (FoT).

Grammar family owned here:
  seven_triplet_rail (canonical: eval task 2b83f449)
    S1: same canvas shape; odd rows carry 777 triplets; even rows are rails.
    S2: each odd-row 777 → 868 (center becomes 6).
    S3: even rails paint 6 at columns of adjacent triplet centers.
    S4: redistribute color-3 markers to segment edges from above-centers;
        suppress conflicting edge-3s across 0-boundaries.
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 2b83f449). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def seven_triplet_rail(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    if len(out) != len(grid) or len(out[0]) != len(grid[0]):
        return None
    return out


def _solve(grid: Grid) -> Grid:
    rows, cols = len(grid), len(grid[0])
    out = [row[:] for row in grid]

    centers: Dict[int, List[int]] = {}
    for r in range(rows):
        if r % 2 != 1:
            continue
        cs: List[int] = []
        c = 0
        while c < cols - 2:
            if grid[r][c] == 7 and grid[r][c + 1] == 7 and grid[r][c + 2] == 7:
                cs.append(c + 1)
                c += 3
            else:
                c += 1
        centers[r] = cs

    for r, cs in centers.items():
        for c in cs:
            out[r][c - 1] = 8
            out[r][c] = 6
            out[r][c + 1] = 8

    for r in range(0, rows, 2):
        above = set(centers.get(r - 1, []))
        below = set(centers.get(r + 1, []))
        all_6_cols = above | below

        for c in all_6_cols:
            out[r][c] = 6

        zeros = sorted(c for c in range(cols) if grid[r][c] == 0)
        boundaries = [-1] + zeros + [cols]
        segments: List[Tuple[int, int]] = []
        for i in range(len(boundaries) - 1):
            s = boundaries[i] + 1
            e = boundaries[i + 1] - 1
            if s <= e:
                segments.append((s, e))

        is_last = r + 2 >= rows

        for seg_s, seg_e in segments:
            is_full_width = seg_s == 0 and seg_e == cols - 1
            sixes: List[Tuple[int, str]] = []
            has_below = False
            for c in range(seg_s, seg_e + 1):
                if c in above:
                    sixes.append((c, "A"))
                elif c in below:
                    sixes.append((c, "B"))
                    has_below = True

            if not sixes:
                continue

            for c in range(seg_s, seg_e + 1):
                if grid[r][c] == 3 and c not in all_6_cols:
                    out[r][c] = 8

            leftmost_s = sixes[0][1]
            rightmost_s = sixes[-1][1]
            can_pair = (not is_last) and (is_full_width or not has_below)

            if leftmost_s == "A":
                out[r][seg_s] = 3
                if can_pair and seg_s == 0:
                    out[r][1] = 3

            if rightmost_s == "A":
                out[r][seg_e] = 3
                if can_pair and seg_e == cols - 1:
                    out[r][seg_e - 1] = 3

        for z in zeros:
            left_seg = right_seg = None
            for seg_s, seg_e in segments:
                if seg_e == z - 1:
                    left_seg = (seg_s, seg_e)
                if seg_s == z + 1:
                    right_seg = (seg_s, seg_e)

            if not (left_seg and right_seg):
                continue
            left_as = [c for c in range(left_seg[0], left_seg[1] + 1) if c in above]
            right_as = [c for c in range(right_seg[0], right_seg[1] + 1) if c in above]
            if not (left_as and right_as):
                continue
            left_has_edge = left_seg[0] == 0 or left_seg[1] == cols - 1
            right_has_edge = right_seg[0] == 0 or right_seg[1] == cols - 1
            if left_has_edge and right_has_edge:
                continue
            if not left_has_edge:
                out[r][left_seg[1]] = 8
            elif not right_has_edge:
                out[r][right_seg[0]] = 8
            else:
                left_nearest = max(left_as)
                right_nearest = min(right_as)
                if (z - left_nearest) <= (right_nearest - z):
                    out[r][left_seg[1]] = 8
                else:
                    out[r][right_seg[0]] = 8

    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("seven_triplet_rail", seven_triplet_rail)]


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
            "engine": "s2_seven_triplet_rail",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_seven_triplet_rail",
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
    "seven_triplet_rail",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
