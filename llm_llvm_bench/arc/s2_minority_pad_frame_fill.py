"""S2 minority pad frame fill (FoT).

Grammar (same_canvas_rewrite):
  Majority nonzero color is the object; least-common nonzero is the frame key.
  Padding is the key's solid-square side length when the key cells form a filled
  square; otherwise the majority-shell thickness (min distance from key bbox to
  majority bbox edge). Expand the majority bbox by that pad and fill zeros with
  the frame/key color (object cells preserved).

Canonical close: AGI-2 test task 3a301edc.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_minority_pad_frame_fill(bg: int = 0) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        cnt = Counter(v for row in inp for v in row if v != bg)
        if len(cnt) < 2:
            return None
        maj = cnt.most_common(1)[0][0]
        frame = min(cnt, key=lambda c: (cnt[c], c))
        if frame == maj:
            return None
        fcells = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == frame]
        mcells = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == maj]
        if not fcells or not mcells:
            return None
        frs = [r for r, _ in fcells]
        fcs = [c for _, c in fcells]
        mrs = [r for r, _ in mcells]
        mcs = [c for _, c in mcells]
        bh = max(frs) - min(frs) + 1
        bw = max(fcs) - min(fcs) + 1
        n = len(fcells)
        mr0, mr1, mc0, mc1 = min(mrs), max(mrs), min(mcs), max(mcs)
        if bh == bw and bh * bw == n:
            pad = bh
        else:
            pad = min(min(frs) - mr0, mr1 - max(frs), min(fcs) - mc0, mc1 - max(fcs))
            if pad < 1:
                return None
        r0, r1 = mr0 - pad, mr1 + pad
        c0, c1 = mc0 - pad, mc1 + pad
        out = [row[:] for row in inp]
        changed = False
        for r in range(max(0, r0), min(h, r1 + 1)):
            for c in range(max(0, c0), min(w, c1 + 1)):
                if out[r][c] == bg:
                    out[r][c] = frame
                    changed = True
        return out if changed else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("minority_pad_frame_fill", make_minority_pad_frame_fill())]


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
            "engine": "s2_minority_pad_frame_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, _ = exact[0]
    passed = len(train)
    return {
        "engine": "s2_minority_pad_frame_fill",
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
