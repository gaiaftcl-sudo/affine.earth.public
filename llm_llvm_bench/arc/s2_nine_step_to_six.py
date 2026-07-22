"""S2 nine step toward six (FoT).

Grammar (same_canvas_rewrite):
  Exactly one 9 and one 6. Clear the 9 back to 5. Move the 9 one step toward
  the 6: if they lie in the same zero-row-separated band, step on the dominant
  axis only; otherwise take a king-step (both axes). Paint the 6 cell to 9.

Canonical close: AGI-2 test task 18286ef8.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_nine_step_to_six() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        zero_rows = {r for r in range(h) if all(v == 0 for v in inp[r])}

        def band_id(r: int) -> int:
            return sum(1 for zr in zero_rows if zr < r)

        nines = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == 9]
        sixes = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == 6]
        if len(nines) != 1 or len(sixes) != 1:
            return None
        r, c = nines[0]
        sr, sc = sixes[0]
        out = [list(row) for row in inp]
        out[r][c] = 5
        same = band_id(r) == band_id(sr)
        if same:
            if abs(sr - r) >= abs(sc - c):
                nr = r if sr == r else (r + 1 if sr > r else r - 1)
                nc = c
            else:
                nr = r
                nc = c if sc == c else (c + 1 if sc > c else c - 1)
        else:
            nr = r if sr == r else (r + 1 if sr > r else r - 1)
            nc = c if sc == c else (c + 1 if sc > c else c - 1)
        if not (0 <= nr < h and 0 <= nc < w):
            return None
        out[nr][nc] = 9
        out[sr][sc] = 9
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("nine_step_to_six", make_nine_step_to_six())]


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
            "engine": "s2_nine_step_to_six",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_nine_step_to_six",
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
