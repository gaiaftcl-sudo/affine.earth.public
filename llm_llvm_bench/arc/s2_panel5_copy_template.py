"""S2 5x5 panel copy-template (FoT).

Grammar (same_canvas_rewrite):
  Detect solid-border 5x5 panels. For each color C with a non-empty
  interior template (max non-zero interior among C panels), copy that
  template interior onto every empty-interior panel of the same color.

Canonical close: AGI-2 test task 42918530.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _panels5(inp: Grid) -> List[Tuple[int, int, int, int]]:
    h, w = len(inp), len(inp[0])
    out: List[Tuple[int, int, int, int]] = []
    for r0 in range(h - 4):
        for c0 in range(w - 4):
            col = inp[r0][c0]
            if col == 0:
                continue
            ok = True
            for i in range(5):
                if (
                    inp[r0][c0 + i] != col
                    or inp[r0 + 4][c0 + i] != col
                    or inp[r0 + i][c0] != col
                    or inp[r0 + i][c0 + 4] != col
                ):
                    ok = False
                    break
            if not ok:
                continue
            nfill = sum(
                1
                for dr in range(1, 4)
                for dc in range(1, 4)
                if inp[r0 + dr][c0 + dc] != 0
            )
            out.append((r0, c0, col, nfill))
    return out


def make_panel5_copy_template() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        pans = _panels5(inp)
        if not pans:
            return None
        by: Dict[int, List[Tuple[int, int, int, int]]] = defaultdict(list)
        for p in pans:
            by[p[2]].append(p)
        out = [row[:] for row in inp]
        changed = False
        for col, lst in by.items():
            tmpl = max(lst, key=lambda p: p[3])
            if tmpl[3] == 0:
                continue
            tr0, tc0 = tmpl[0], tmpl[1]
            for r0, c0, _c, nf in lst:
                if nf != 0:
                    continue
                for dr in range(1, 4):
                    for dc in range(1, 4):
                        out[r0 + dr][c0 + dc] = inp[tr0 + dr][tc0 + dc]
                changed = True
        return out if changed else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("panel5_copy_template", make_panel5_copy_template())]


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
            "engine": "s2_panel5_copy_template",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_panel5_copy_template",
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
