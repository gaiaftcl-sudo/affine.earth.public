"""S1 2x2 block pack (FoT).

Grammar (zoom_in_crop):
  Find solid 2×2 blocks (non-zero, non-frame color 8). Pack their colors into
  a compact grid ordered by block row/col.

Canonical close: AGI-2 test task 19bb5feb.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _learn_frame(train: Sequence[Dict[str, Any]]) -> Optional[int]:
    votes = Counter()
    for example in train:
        gi = example["input"]
        votes[Counter(c for row in gi for c in row if c != 0).most_common(1)[0][0]] += 1
    if len(votes) != 1:
        return None
    return votes.most_common(1)[0][0]


def make_pack(frame: int) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        blocks: List[Tuple[int, int, int]] = []
        claimed = set()
        for r in range(h - 1):
            for c in range(w - 1):
                if (r, c) in claimed:
                    continue
                vals = [inp[r][c], inp[r][c + 1], inp[r + 1][c], inp[r + 1][c + 1]]
                if any(v == 0 or v == frame for v in vals):
                    continue
                if len(set(vals)) != 1:
                    continue
                blocks.append((r, c, vals[0]))
                claimed.update({(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)})
        if not blocks:
            return None
        blocks.sort()
        brows = sorted({b[0] for b in blocks})
        bcols = sorted({b[1] for b in blocks})
        rm = {r: i for i, r in enumerate(brows)}
        cm = {c: i for i, c in enumerate(bcols)}
        out = [[0] * len(bcols) for _ in range(len(brows))]
        for r, c, col in blocks:
            out[rm[r]][cm[c]] = col
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    frame = _learn_frame(train)
    if frame is None:
        return []
    return [("twobytwo_block_pack", make_pack(frame))]


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
            "engine": "s1_twobytwo_block_pack",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_twobytwo_block_pack",
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
