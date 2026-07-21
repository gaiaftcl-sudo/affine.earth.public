"""S1 separator-row motif progress (FoT).

Grammar (zoom_in_crop):
  Solid separator rows (color 5) split panels. Read one motif row per panel;
  extrapolate start/length (or shifted pattern) one step; emit empty/motif/empty.

Canonical close: AGI-2 test task 351d6448.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _learn_sep(train: Sequence[Dict[str, Any]]) -> Optional[int]:
    votes = Counter()
    for example in train:
        gi = example["input"]
        h, w = len(gi), len(gi[0])
        seps = [
            r
            for r in range(h)
            if len(set(gi[r])) == 1 and gi[r][0] != 0 and all(x == gi[r][0] for x in gi[r])
        ]
        if not seps:
            return None
        votes[gi[seps[0]][0]] += 1
    if len(votes) != 1:
        return None
    return votes.most_common(1)[0][0]


def make_progress(sep: int) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        seps = [r for r in range(h) if all(inp[r][c] == sep for c in range(w))]
        if not seps:
            return None
        panels: List[Grid] = []
        prev = 0
        for sr in seps + [h]:
            panel = inp[prev:sr]
            if panel:
                panels.append(panel)
            prev = sr + 1
        motifs: List[List[int]] = []
        for panel in panels:
            for row in panel:
                if any(x != 0 for x in row):
                    motifs.append(list(row))
                    break
        if len(motifs) < 2:
            return None

        def span(row: List[int]) -> Optional[Tuple[int, int, List[int]]]:
            idx = [i for i, c in enumerate(row) if c != 0]
            if not idx:
                return None
            return idx[0], idx[-1], row[idx[0] : idx[-1] + 1]

        spans = [span(m) for m in motifs]
        if any(s is None for s in spans):
            return None
        starts = [s[0] for s in spans]  # type: ignore[index]
        lens = [s[1] - s[0] + 1 for s in spans]  # type: ignore[index]
        ds = starts[1] - starts[0]
        if not all(starts[i + 1] - starts[i] == ds for i in range(len(starts) - 1)):
            return None
        dl = lens[1] - lens[0]
        if not all(lens[i + 1] - lens[i] == dl for i in range(len(lens) - 1)):
            return None
        next_start = starts[-1] + ds
        next_len = lens[-1] + dl
        last = spans[-1][2]  # type: ignore[index]
        out_row = [0] * w
        if len(set(last)) == 1:
            color = last[0]
            for i in range(next_len):
                if 0 <= next_start + i < w:
                    out_row[next_start + i] = color
        else:
            for i, v in enumerate(last):
                if 0 <= next_start + i < w:
                    out_row[next_start + i] = v
        return [[0] * w, out_row, [0] * w]

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    sep = _learn_sep(train)
    if sep is None:
        return []
    return [("sep_row_motif_progress", make_progress(sep))]


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
            "engine": "s1_sep_row_motif_progress",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_sep_row_motif_progress",
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
