"""S2 host vertical-symmetry bbox complete (FoT).

Grammar (same_canvas_rewrite):
  Majority non-zero color is the host. Clear every other color. Complete the
  host silhouette to vertical mirror symmetry across the host column bbox
  midline (c' = c_min + c_max - c).

Canonical close: AGI-2 test task 3345333e.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_host_vsym_bbox_complete(bg: int = 0) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        cnt = Counter(v for row in inp for v in row if v != bg)
        if len(cnt) < 2:
            return None
        host = cnt.most_common(1)[0][0]
        host_cells = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == host]
        if not host_cells:
            return None
        cs = [c for _, c in host_cells]
        c0, c1 = min(cs), max(cs)
        out = [[bg] * w for _ in range(h)]
        changed = False
        for r, c in host_cells:
            out[r][c] = host
            mc = c0 + c1 - c
            if 0 <= mc < w:
                if out[r][mc] != host:
                    changed = True
                out[r][mc] = host
        # Must clear intruder / rewrite canvas
        if out == inp:
            return None
        return out if (changed or any(inp[r][c] not in (bg, host) for r in range(h) for c in range(w))) else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("host_vsym_bbox_complete", make_host_vsym_bbox_complete())]


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
            "engine": "s2_host_vsym_bbox_complete",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_host_vsym_bbox_complete",
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
