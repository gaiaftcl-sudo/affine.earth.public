"""S2 marker-sprite recolor (FoT).

Grammar (same_canvas_rewrite):
  - Color-1 cells form a small marker sprite (bbox fingerprint).
  - Color-8 (fill) cells are recolored to a target color keyed by that sprite.
  - Marker cells clear to 0.

Canonical close: AGI-2 test task 009d5c81 (14×14, 5 demos).
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

MARKER = 1
FILL = 8


def _sprite_key(grid: Grid) -> Optional[Tuple[Tuple[int, ...], ...]]:
    ones = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == MARKER]
    if not ones:
        return None
    rs = [r for r, _ in ones]
    cs = [c for _, c in ones]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    ones_set = set(ones)
    return tuple(
        tuple(1 if (r, c) in ones_set else 0 for c in range(c0, c1 + 1))
        for r in range(r0, r1 + 1)
    )


def _learn_sprite_to_color(train: Sequence[Dict[str, Any]]) -> Optional[Dict[Tuple, int]]:
    mapping: Dict[Tuple, int] = {}
    for ex in train:
        inp, out = ex["input"], ex["output"]
        if len(inp) != len(out) or (inp and len(inp[0]) != len(out[0])):
            return None
        key = _sprite_key(inp)
        if key is None:
            return None
        fills = [(r, c) for r, row in enumerate(inp) for c, v in enumerate(row) if v == FILL]
        if not fills:
            return None
        targets = {out[r][c] for r, c in fills}
        if len(targets) != 1:
            return None
        tgt = next(iter(targets))
        if key in mapping and mapping[key] != tgt:
            return None
        mapping[key] = tgt
        # Marker must clear; non-fill/non-marker unchanged
        for r, row in enumerate(inp):
            for c, v in enumerate(row):
                if v == MARKER and out[r][c] != 0:
                    return None
                if v not in (MARKER, FILL) and out[r][c] != v:
                    return None
    return mapping or None


def marker_sprite_recolor(inp: Grid, mapping: Dict[Tuple, int]) -> Optional[Grid]:
    key = _sprite_key(inp)
    if key is None or key not in mapping:
        return None
    tgt = mapping[key]
    out = [list(row) for row in inp]
    for r, row in enumerate(inp):
        for c, v in enumerate(row):
            if v == FILL:
                out[r][c] = tgt
            elif v == MARKER:
                out[r][c] = 0
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    mapping = _learn_sprite_to_color(train)
    if mapping is None:
        return []

    def _xf(grid: Grid) -> Optional[Grid]:
        return marker_sprite_recolor(grid, mapping)

    return [("marker_sprite_recolor", _xf)]


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
            "engine": "s2_marker_sprite_recolor",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_marker_sprite_recolor",
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
    "marker_sprite_recolor",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
