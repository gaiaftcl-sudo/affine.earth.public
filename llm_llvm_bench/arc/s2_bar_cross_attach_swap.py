"""S2 bar cross-attach swap (FoT).

Grammar (same_canvas_rewrite):
  Dominant run color is the bar (horizontal band or vertical pillar).
  On each line orthogonal to the bar: if markers exist on BOTH sides of that
  line's bar segment, swap them to the opposite side and seat them immediately
  adjacent to the bar. If only one side has markers, leave them in place.

Canonical close: AGI-2 test task 1efba499.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _bar_color(inp: Grid, bg: int = 0) -> Optional[int]:
    cnt = Counter(v for row in inp for v in row if v != bg)
    if not cnt:
        return None
    h, w = len(inp), len(inp[0])
    best: Optional[Tuple[int, int, int]] = None
    for col, n in cnt.most_common():
        for r in range(h):
            run = sum(1 for c in range(w) if inp[r][c] == col)
            sc = (run, n, col)
            if best is None or sc > best:
                best = sc
        for c in range(w):
            run = sum(1 for r in range(h) if inp[r][c] == col)
            sc = (run, n, col)
            if best is None or sc > best:
                best = sc
    return best[2] if best else None


def make_bar_cross_attach_swap(bg: int = 0) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        bar = _bar_color(inp, bg=bg)
        if bar is None:
            return None
        row_runs = max(sum(1 for c in range(w) if inp[r][c] == bar) for r in range(h))
        col_runs = max(sum(1 for r in range(h) if inp[r][c] == bar) for c in range(w))
        vertical = col_runs >= row_runs
        out = [[bar if inp[r][c] == bar else bg for c in range(w)] for r in range(h)]
        changed = False
        if vertical:
            for r in range(h):
                cols_bar = [c for c in range(w) if inp[r][c] == bar]
                if not cols_bar:
                    for c in range(w):
                        if inp[r][c] not in (bg, bar):
                            out[r][c] = inp[r][c]
                    continue
                c0, c1 = min(cols_bar), max(cols_bar)
                left = [(c, inp[r][c]) for c in range(w) if inp[r][c] not in (bg, bar) and c < c0]
                right = [(c, inp[r][c]) for c in range(w) if inp[r][c] not in (bg, bar) and c > c1]
                if left and right:
                    left_sorted = sorted(left)
                    right_sorted = sorted(right)
                    if len(left_sorted) == 1 and len(right_sorted) == 1:
                        targets = [(c1 + 1, left_sorted[0][1]), (c0 - 1, right_sorted[0][1])]
                    else:
                        targets = []
                        for i, (_, col) in enumerate(left_sorted):
                            targets.append((c1 + 1 + i, col))
                        for i, (_, col) in enumerate(reversed(right_sorted)):
                            targets.append((c0 - 1 - i, col))
                    for nc, col in targets:
                        if 0 <= nc < w:
                            out[r][nc] = col
                            changed = True
                else:
                    for c, col in left + right:
                        out[r][c] = col
        else:
            for c in range(w):
                rows_bar = [r for r in range(h) if inp[r][c] == bar]
                if not rows_bar:
                    for r in range(h):
                        if inp[r][c] not in (bg, bar):
                            out[r][c] = inp[r][c]
                    continue
                r0, r1 = min(rows_bar), max(rows_bar)
                above = [(r, inp[r][c]) for r in range(h) if inp[r][c] not in (bg, bar) and r < r0]
                below = [(r, inp[r][c]) for r in range(h) if inp[r][c] not in (bg, bar) and r > r1]
                if above and below:
                    above_sorted = sorted(above)
                    below_sorted = sorted(below)
                    if len(above_sorted) == 1 and len(below_sorted) == 1:
                        targets = [(r1 + 1, above_sorted[0][1]), (r0 - 1, below_sorted[0][1])]
                    else:
                        targets = []
                        for i, (_, col) in enumerate(above_sorted):
                            targets.append((r1 + 1 + i, col))
                        for i, (_, col) in enumerate(reversed(below_sorted)):
                            targets.append((r0 - 1 - i, col))
                    for nr, col in targets:
                        if 0 <= nr < h:
                            out[nr][c] = col
                            changed = True
                else:
                    for r, col in above + below:
                        out[r][c] = col
        if out == inp:
            return None
        return out if changed or out != inp else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("bar_cross_attach_swap", make_bar_cross_attach_swap())]


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
            "engine": "s2_bar_cross_attach_swap",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_bar_cross_attach_swap",
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
