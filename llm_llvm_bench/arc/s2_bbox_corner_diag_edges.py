"""S2 bbox corner diagonal + empty-corner edges (FoT).

Grammar (same_canvas_rewrite):
  Take the bounding box of all color-5 markers. Among the four bbox corners,
  find the opposite pair that both hold a 5; paint that diagonal with 8s.
  Exactly one bbox corner lacks a 5; paint the two bbox edges from that empty
  corner with 8s. Never overwrite 5s.

Canonical close: AGI-2 test task 1478ab18.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_bbox_corner_diag_edges() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        fives = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == 5]
        if len(fives) < 2:
            return None
        rs = [r for r, _ in fives]
        cs = [c for _, c in fives]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        corners = {
            "tl": (r0, c0),
            "tr": (r0, c1),
            "bl": (r1, c0),
            "br": (r1, c1),
        }
        has = {k: inp[r][c] == 5 for k, (r, c) in corners.items()}
        diag_pair = None
        for a, b in (("tl", "br"), ("tr", "bl")):
            if has[a] and has[b]:
                diag_pair = (a, b)
                break
        if diag_pair is None:
            return None
        empty = [k for k, v in has.items() if not v]
        if len(empty) != 1:
            return None
        empty_corner = empty[0]
        out = [list(row) for row in inp]

        def paint(r: int, c: int) -> None:
            if 0 <= r < h and 0 <= c < w and out[r][c] != 5:
                out[r][c] = 8

        ra, ca = corners[diag_pair[0]]
        rb, cb = corners[diag_pair[1]]
        steps = max(abs(rb - ra), abs(cb - ca))
        if steps == 0:
            paint(ra, ca)
        else:
            for i in range(steps + 1):
                paint(ra + (rb - ra) * i // steps, ca + (cb - ca) * i // steps)
        if empty_corner == "tl":
            for c in range(c0, c1 + 1):
                paint(r0, c)
            for r in range(r0, r1 + 1):
                paint(r, c0)
        elif empty_corner == "tr":
            for c in range(c0, c1 + 1):
                paint(r0, c)
            for r in range(r0, r1 + 1):
                paint(r, c1)
        elif empty_corner == "bl":
            for c in range(c0, c1 + 1):
                paint(r1, c)
            for r in range(r0, r1 + 1):
                paint(r, c0)
        else:
            for c in range(c0, c1 + 1):
                paint(r1, c)
            for r in range(r0, r1 + 1):
                paint(r, c1)
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("bbox_corner_diag_edges", make_bbox_corner_diag_edges())]


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
            "engine": "s2_bbox_corner_diag_edges",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_bbox_corner_diag_edges",
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
