"""S1 motif cardinal dihedral expand (FoT).

Grammar (zoom_out_expand):
  Crop the nonzero motif. Build an N×N canvas with
  N = 2·max(h,w) + min(h,w). Stamp the motif on the left,
  its horizontal flip on the right, rot90 on top, rot270 on bottom
  (centered on the free axis).

Canonical close: AGI-2 test task 2697da3f.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _crop_nz(inp: Grid, bg: int = 0) -> Optional[Grid]:
    h, w = len(inp), len(inp[0])
    rs = [r for r in range(h) if any(inp[r][c] != bg for c in range(w))]
    cs = [c for c in range(w) if any(inp[r][c] != bg for r in range(h))]
    if not rs or not cs:
        return None
    return [list(inp[r][cs[0] : cs[-1] + 1]) for r in range(rs[0], rs[-1] + 1)]


def _rot90(g: Grid) -> Grid:
    h, w = len(g), len(g[0])
    return [[g[h - 1 - r][c] for r in range(h)] for c in range(w)]


def _flip_h(g: Grid) -> Grid:
    return [list(reversed(row)) for row in g]


def _stamp(canvas: Grid, motif: Grid, r0: int, c0: int) -> None:
    for r in range(len(motif)):
        for c in range(len(motif[0])):
            if motif[r][c] != 0:
                canvas[r0 + r][c0 + c] = motif[r][c]


def motif_cardinal_dihedral(inp: Grid, bg: int = 0) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    motif = _crop_nz(inp, bg)
    if motif is None:
        return None
    mh, mw = len(motif), len(motif[0])
    n = 2 * max(mh, mw) + min(mh, mw)
    out: Grid = [[bg] * n for _ in range(n)]
    r90 = _rot90(motif)
    r270 = _rot90(_rot90(r90))
    _stamp(out, motif, (n - mh) // 2, 0)
    _stamp(out, _flip_h(motif), (n - mh) // 2, n - mw)
    _stamp(out, r90, 0, (n - len(r90[0])) // 2)
    _stamp(out, r270, n - len(r270), (n - len(r270[0])) // 2)
    return out


def make_motif_cardinal_dihedral() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return motif_cardinal_dihedral(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("motif_cardinal_dihedral", make_motif_cardinal_dihedral())]


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
            "engine": "s1_motif_cardinal_dihedral",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_motif_cardinal_dihedral",
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
    "motif_cardinal_dihedral",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
