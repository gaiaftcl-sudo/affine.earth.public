"""S1 marker-pair recolor stack (FoT).

Grammar (zoom_in_crop): zero-row-separated blocks; one template block of a
twin left/right motif (split by a zero column) and one marker block. Each
marker row that introduces foreign colors yields a (left_color, right_color)
pair. Emit recolored template copies stacked with template-color separators.
Recolor: template_color→pair color; holes 0→template_color.

Canonical close: AGI-2 test task 1be83260.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _split_blocks(inp: Grid) -> List[Grid]:
    blocks: List[Grid] = []
    cur: Grid = []
    for row in inp:
        if all(v == 0 for v in row):
            if cur:
                blocks.append(cur)
                cur = []
        else:
            cur.append(list(row))
    if cur:
        blocks.append(cur)
    return blocks


def _trim(block: Grid) -> Grid:
    cols = [c for c in range(len(block[0])) if any(row[c] != 0 for row in block)]
    if not cols:
        return [list(row) for row in block]
    c0, c1 = cols[0], cols[-1]
    return [row[c0 : c1 + 1] for row in block]


def _lr_split(panel: Grid) -> Tuple[Grid, Grid]:
    w = len(panel[0])
    for c in range(w):
        if all(row[c] == 0 for row in panel):
            return [row[:c] for row in panel], [row[c + 1 :] for row in panel]
    mid = w // 2
    return [row[:mid] for row in panel], [row[mid + 1 :] for row in panel]


def _recolor(panel: Grid, color: int, tc: int) -> Grid:
    return [[(color if v == tc else (tc if v == 0 else v)) for v in row] for row in panel]


def marker_pair_stack(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    blocks = _split_blocks(inp)
    if len(blocks) < 2:
        return None
    trimmed = [_trim(b) for b in blocks]
    flat = [v for row in trimmed[0] for v in row if v != 0]
    if not flat:
        return None
    tc = Counter(flat).most_common(1)[0][0]
    marker: Optional[Grid] = None
    template: Optional[Grid] = None
    for b in trimmed:
        foreign = set(v for row in b for v in row) - {0, tc}
        if foreign:
            marker = b
        else:
            template = b
    if template is None:
        template = trimmed[0]
    if marker is None:
        return None
    left_t, right_t = _lr_split(template)
    left_m, right_m = _lr_split(marker)
    if not left_t or not right_t or len(left_t[0]) == 0 or len(right_t[0]) == 0:
        return None
    pairs: List[Tuple[int, int]] = []
    for r in range(len(marker)):
        left_f: List[int] = []
        right_f: List[int] = []
        for v in left_m[r]:
            if v not in (0, tc) and v not in left_f:
                left_f.append(v)
        for v in right_m[r]:
            if v not in (0, tc) and v not in right_f:
                right_f.append(v)
        if not left_f and not right_f:
            continue
        if left_f and right_f:
            cl, cr = left_f[0], right_f[0]
        elif left_f:
            cl = left_f[0]
            cr = left_f[1] if len(left_f) > 1 else tc
        else:
            cl = right_f[0]
            cr = right_f[1] if len(right_f) > 1 else tc
        pairs.append((cl, cr))
    if not pairs:
        return None
    out: Grid = []
    width = len(left_t[0]) + 1 + len(right_t[0])
    for i, (cl, cr) in enumerate(pairs):
        if i:
            out.append([tc] * width)
        left = _recolor(left_t, cl, tc)
        right = _recolor(right_t, cr, tc)
        for lr, rr in zip(left, right):
            out.append(lr + [tc] + rr)
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    if not train or not all(marker_pair_stack(ex["input"]) == ex["output"] for ex in train):
        return []

    def _xf(grid: Grid) -> Optional[Grid]:
        return marker_pair_stack(grid)

    return [("marker_pair_recolor_stack", _xf)]


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
            "engine": "s1_marker_pair_recolor_stack",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_marker_pair_recolor_stack",
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
    "marker_pair_stack",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
