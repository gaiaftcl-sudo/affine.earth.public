"""S2 separator-panel template stamp (FoT).

Grammar (same_canvas_rewrite):
  Find a tall column of 5s (separator). The nonzero block left of it (excluding
  1-markers) is the template. Each 1 marker stamps the template at
  (marker_row-1, marker_col-1). Markers are cleared; the separator column is
  restored.

Canonical close: AGI-2 test task 363442ee.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_stamp(sep_color: int = 5, marker: int = 1) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h, w = len(inp), len(inp[0])
        sep = None
        for c in range(w):
            if sum(1 for r in range(h) if inp[r][c] == sep_color) >= max(3, h // 2):
                sep = c
                break
        if sep is None:
            return None
        cells = [
            (r, c)
            for r in range(h)
            for c in range(sep)
            if inp[r][c] not in (0, sep_color, marker)
        ]
        if not cells:
            return None
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        template = [row[c0 : c1 + 1] for row in inp[r0 : r1 + 1]]
        th, tw = r1 - r0 + 1, c1 - c0 + 1
        markers = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == marker]
        out = [row[:] for row in inp]
        for r, c in markers:
            out[r][c] = 0
        for mr, mc in markers:
            sr, sc = mr - 1, mc - 1
            for i in range(th):
                for j in range(tw):
                    nr, nc = sr + i, sc + j
                    if 0 <= nr < h and 0 <= nc < w:
                        out[nr][nc] = template[i][j]
        for r in range(h):
            if inp[r][sep] == sep_color:
                out[r][sep] = sep_color
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("sep_panel_template_stamp", make_stamp())]


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
            "engine": "s2_sep_panel_template_stamp",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_sep_panel_template_stamp",
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
