"""S1 separator panel feature stack (FoT).

Grammar (zoom_in_crop):
  Solid separator columns (color 6) split equal-width panels. Collect non-bg
  (non-7) rows from panels in right-to-left order; pad with solid-7 rows to
  panel height.

Canonical close: AGI-2 test task 25c199f5.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _learn(train: Sequence[Dict[str, Any]]) -> Optional[Tuple[int, int]]:
    sep_votes = Counter()
    bg_votes = Counter()
    for example in train:
        gi, go = example["input"], example["output"]
        h, w = len(gi), len(gi[0])
        if len(go) != h:
            return None
        found = None
        for sep in range(10):
            seps = [c for c in range(w) if all(gi[r][c] == sep for r in range(h))]
            if len(seps) < 1:
                continue
            widths = []
            prev = 0
            for sc in seps + [w]:
                widths.append(sc - prev)
                prev = sc + 1
            if len(widths) >= 2 and len(set(widths)) == 1 and widths[0] > 0:
                found = (sep, seps)
                break
        if found is None:
            return None
        sep, _ = found
        sep_votes[sep] += 1
        bg = Counter(c for row in gi for c in row if c != sep).most_common(1)[0][0]
        bg_votes[bg] += 1
    if len(sep_votes) != 1 or len(bg_votes) != 1:
        return None
    return sep_votes.most_common(1)[0][0], bg_votes.most_common(1)[0][0]


def make_stack(sep: int, bg: int) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        seps = [c for c in range(w) if all(inp[r][c] == sep for r in range(h))]
        if not seps:
            return None
        panels: List[Grid] = []
        prev = 0
        for sc in seps + [w]:
            panel = [list(row[prev:sc]) for row in inp]
            if not panel or not panel[0]:
                return None
            panels.append(panel)
            prev = sc + 1
        if len(panels) < 2:
            return None
        pw = len(panels[0][0])
        if any(len(p[0]) != pw for p in panels):
            return None
        rows: List[List[int]] = []
        for panel in reversed(panels):
            for row in panel:
                if any(x != bg for x in row):
                    rows.append(list(row))
        while len(rows) < h:
            rows.insert(0, [bg] * pw)
        return rows[:h]

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    learned = _learn(train)
    if learned is None:
        return []
    sep, bg = learned
    return [("sep_panel_feature_stack", make_stack(sep, bg))]


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
            "engine": "s1_sep_panel_feature_stack",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_sep_panel_feature_stack",
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
