"""S2 mirror across full separator (FoT).

Grammar (same_canvas_rewrite):
  Find a full horizontal or vertical separator of a single nonzero color with
  content on exactly one side. Mirror that content across the separator onto
  the empty side. Recolor the source motif via a pairwise color map learned
  from train (cells that change color while remaining nonzero).

Canonical close: AGI-2 test task 2b01abd0.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _learn_cmap(train: Sequence[Dict[str, Any]]) -> Dict[int, int]:
    cmap: Dict[int, int] = {}
    for ex in train:
        inp, out = ex["input"], ex["output"]
        if len(inp) != len(out) or (inp and len(inp[0]) != len(out[0])):
            continue
        h, w = len(inp), len(inp[0])
        for r in range(h):
            for c in range(w):
                a, b = inp[r][c], out[r][c]
                if a != 0 and b != 0 and a != b:
                    cmap[a] = b
    return cmap


def make_mirror_across_full_sep(cmap: Dict[int, int]) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        out = [list(row) for row in inp]
        for r in range(h):
            if len(set(inp[r])) == 1 and inp[r][0] != 0:
                above = any(inp[rr][c] != 0 for rr in range(r) for c in range(w))
                below = any(inp[rr][c] != 0 for rr in range(r + 1, h) for c in range(w))
                if above ^ below:
                    src = range(r) if above else range(r + 1, h)
                    for rr in src:
                        for c in range(w):
                            v = inp[rr][c]
                            if v == 0:
                                continue
                            dest = r + (r - rr)
                            if 0 <= dest < h:
                                out[dest][c] = v
                            out[rr][c] = cmap.get(v, v)
                    return out
        for c in range(w):
            colset = {inp[r][c] for r in range(h)}
            if len(colset) == 1 and inp[0][c] != 0:
                left = any(inp[r][cc] != 0 for r in range(h) for cc in range(c))
                right = any(inp[r][cc] != 0 for r in range(h) for cc in range(c + 1, w))
                if left ^ right:
                    src = range(c) if left else range(c + 1, w)
                    for r in range(h):
                        for cc in src:
                            v = inp[r][cc]
                            if v == 0:
                                continue
                            dest = c + (c - cc)
                            if 0 <= dest < w:
                                out[r][dest] = v
                            out[r][cc] = cmap.get(v, v)
                    return out
        return None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    if not train:
        return []
    cmap = _learn_cmap(train)
    if not cmap:
        return []
    return [("mirror_across_full_sep", make_mirror_across_full_sep(cmap))]


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
            "engine": "s2_mirror_across_full_sep",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_mirror_across_full_sep",
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
