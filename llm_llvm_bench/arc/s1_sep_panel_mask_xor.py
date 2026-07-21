"""S1 separator panel mask XOR (FoT).

Grammar (zoom_in_crop):
  A solid separator (column of 4 or row of 4) splits two equal panels.
  Output is the XOR of the two nonzero masks, painted with a learned color.

Canonical closes: AGI-2 test tasks 34b99a2b (col-sep), 3428a4f5 (row-sep).
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _learn(train: Sequence[Dict[str, Any]]) -> Optional[Tuple[str, int, int]]:
    """Return (axis, sep_color, fill_color)."""
    axes = Counter()
    sep_votes = Counter()
    fill_votes = Counter()
    for example in train:
        gi, go = example["input"], example["output"]
        ih, iw = len(gi), len(gi[0])
        oh, ow = len(go), len(go[0])
        fills = {c for row in go for c in row if c != 0}
        if len(fills) != 1:
            return None
        fill = next(iter(fills))
        fill_votes[fill] += 1
        # column separator
        for sc in range(iw):
            col = [gi[r][sc] for r in range(ih)]
            if len(set(col)) == 1 and col[0] != 0:
                left_w, right_w = sc, iw - sc - 1
                if left_w == right_w == ow and oh == ih:
                    axes["col"] += 1
                    sep_votes[col[0]] += 1
                    break
        else:
            # row separator
            for sr in range(ih):
                row = gi[sr]
                if len(set(row)) == 1 and row[0] != 0:
                    top_h, bot_h = sr, ih - sr - 1
                    if top_h == bot_h == oh and ow == iw:
                        axes["row"] += 1
                        sep_votes[row[0]] += 1
                        break
            else:
                return None
    if len(axes) != 1 or len(sep_votes) != 1 or len(fill_votes) != 1:
        return None
    return axes.most_common(1)[0][0], sep_votes.most_common(1)[0][0], fill_votes.most_common(1)[0][0]


def make_xor(axis: str, sep_color: int, fill: int) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        if axis == "col":
            sc = None
            for c in range(w):
                col = [inp[r][c] for r in range(h)]
                if len(set(col)) == 1 and col[0] == sep_color:
                    sc = c
                    break
            if sc is None:
                return None
            left_w, right_w = sc, w - sc - 1
            if left_w != right_w or left_w == 0:
                return None
            out = [[0] * left_w for _ in range(h)]
            for r in range(h):
                for c in range(left_w):
                    a = inp[r][c] != 0
                    b = inp[r][sc + 1 + c] != 0
                    if a ^ b:
                        out[r][c] = fill
            return out
        # row
        sr = None
        for r in range(h):
            row = inp[r]
            if len(set(row)) == 1 and row[0] == sep_color:
                sr = r
                break
        if sr is None:
            return None
        top_h, bot_h = sr, h - sr - 1
        if top_h != bot_h or top_h == 0:
            return None
        out = [[0] * w for _ in range(top_h)]
        for r in range(top_h):
            for c in range(w):
                a = inp[r][c] != 0
                b = inp[sr + 1 + r][c] != 0
                if a ^ b:
                    out[r][c] = fill
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    learned = _learn(train)
    if learned is None:
        return []
    axis, sep, fill = learned
    return [(f"sep_panel_mask_xor_{axis}", make_xor(axis, sep, fill))]


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
            "engine": "s1_sep_panel_mask_xor",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_sep_panel_mask_xor",
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
    "solve_task",
    "submission_fragment",
    "train_replay",
]
