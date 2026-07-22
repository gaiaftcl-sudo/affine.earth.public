"""S2 mask-5 template row select (FoT).

Grammar (crop_rewrite):
  Input has a 5-mask region and a 3-row colored template of equal width.
  Two of the three template rows are the pattern; the remaining row is fill
  (often uniform). Output is the mask bbox: pattern[c] where mask cell is 5,
  else fill[c].

Canonical close: AGI-2 test task 278e5215.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_mask5_template_row_select() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        fives = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == 5]
        other = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if inp[r][c] not in (0, 5)
        ]
        if not fives or not other:
            return None
        rs = [r for r, _ in fives]
        cs = [c for _, c in fives]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        trs = [r for r, _ in other]
        tcs = [c for _, c in other]
        tr0, tr1, tc0, tc1 = min(trs), max(trs), min(tcs), max(tcs)
        mh, mw = r1 - r0 + 1, c1 - c0 + 1
        th, tw = tr1 - tr0 + 1, tc1 - tc0 + 1
        if tw != mw or th != 3:
            return None
        templ = [
            [inp[r][c] for c in range(tc0, tc1 + 1)] for r in range(tr0, tr1 + 1)
        ]
        if templ[0] == templ[1]:
            pattern, fill = templ[0], templ[2]
        elif templ[0] == templ[2]:
            pattern, fill = templ[0], templ[1]
        elif templ[1] == templ[2]:
            pattern, fill = templ[1], templ[0]
        else:

            def unif(row: List[int]) -> int:
                return Counter(row).most_common(1)[0][1]

            order = sorted(range(3), key=lambda i: -unif(templ[i]))
            fill = templ[order[0]]
            pattern = templ[order[1]]
        out: Grid = []
        for r in range(r0, r1 + 1):
            row: List[int] = []
            for j, c in enumerate(range(c0, c1 + 1)):
                row.append(pattern[j] if inp[r][c] == 5 else fill[j])
            out.append(row)
        if len(out) != mh:
            return None
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("mask5_template_row_select", make_mask5_template_row_select())]


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
            "engine": "s2_mask5_template_row_select",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_mask5_template_row_select",
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
