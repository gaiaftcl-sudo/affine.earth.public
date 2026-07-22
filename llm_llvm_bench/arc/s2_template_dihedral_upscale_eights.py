"""S2 template dihedral upscale onto eights (FoT).

Grammar (same_canvas_rewrite):
  Non-{0,8} cells form a compact template. Color-8 cells form a target mask
  whose bbox is an integer multiple of the template size. A single dihedral of
  the template, nearest-neighbor upscaled to the eight-bbox, paints every 8
  (zeros in the upscale over an 8 are rejected). Template cells stay put.
  Licensed only on perfect train replay (shared dihedral index).

Canonical close: AGI-2 test task 103eff5b.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _rot90_cw(g: Grid) -> Grid:
    h, w = len(g), len(g[0])
    out: Grid = [[0] * h for _ in range(w)]
    for r in range(h):
        for c in range(w):
            out[c][h - 1 - r] = g[r][c]
    return out


def _dihedral(g: Grid) -> List[Grid]:
    uniq: List[Grid] = []
    seen = set()
    cur = g
    for _ in range(4):
        for v in (
            cur,
            cur[::-1],
            [row[::-1] for row in cur],
            [row[::-1] for row in cur][::-1],
        ):
            key = tuple(tuple(row) for row in v)
            if key not in seen:
                seen.add(key)
                uniq.append([row[:] for row in v])
        cur = _rot90_cw(cur)
    return uniq


def _upscale(g: Grid, height: int, width: int) -> Optional[Grid]:
    gh, gw = len(g), len(g[0])
    if gh == 0 or gw == 0 or height % gh != 0 or width % gw != 0:
        return None
    br, bc = height // gh, width // gw
    out: Grid = [[0] * width for _ in range(height)]
    for r in range(gh):
        for c in range(gw):
            val = g[r][c]
            for i in range(br):
                for j in range(bc):
                    out[r * br + i][c * bc + j] = val
    return out


def _extract(inp: Grid) -> Optional[Tuple[Grid, List[Tuple[int, int]], int, int]]:
    h, w = len(inp), len(inp[0])
    tmpl_cells = [
        (r, c, inp[r][c])
        for r in range(h)
        for c in range(w)
        if inp[r][c] not in (0, 8)
    ]
    eights = [(r, c) for r in range(h) for c in range(w) if inp[r][c] == 8]
    if not tmpl_cells or not eights:
        return None
    trs = [r for r, _, _ in tmpl_cells]
    tcs = [c for _, c, _ in tmpl_cells]
    tr0, tr1, tc0, tc1 = min(trs), max(trs), min(tcs), max(tcs)
    th, tw = tr1 - tr0 + 1, tc1 - tc0 + 1
    tmpl: Grid = [[0] * tw for _ in range(th)]
    for r, c, v in tmpl_cells:
        tmpl[r - tr0][c - tc0] = v
    ers = [r for r, _ in eights]
    ecs = [c for _, c in eights]
    er0, er1, ec0, ec1 = min(ers), max(ers), min(ecs), max(ecs)
    return tmpl, eights, er0, ec0


def make_template_dihedral_upscale_eights(dihedral_index: int) -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        extracted = _extract(inp)
        if extracted is None:
            return None
        tmpl, eights, er0, ec0 = extracted
        variants = _dihedral(tmpl)
        if dihedral_index < 0 or dihedral_index >= len(variants):
            return None
        ers = [r for r, _ in eights]
        ecs = [c for _, c in eights]
        U = _upscale(variants[dihedral_index], max(ers) - min(ers) + 1, max(ecs) - min(ecs) + 1)
        if U is None:
            return None
        out = [row[:] for row in inp]
        for r, c in eights:
            v = U[r - er0][c - ec0]
            if v == 0:
                return None
            out[r][c] = v
        return out if out != inp else None

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    # Probe first train example for how many dihedral slots exist.
    if not train:
        return []
    extracted = _extract(train[0]["input"])
    if extracted is None:
        return []
    n = len(_dihedral(extracted[0]))
    return [
        (f"template_dihedral_upscale_eights_{i}", make_template_dihedral_upscale_eights(i))
        for i in range(n)
    ]


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
            "engine": "s2_template_dihedral_upscale_eights",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_template_dihedral_upscale_eights",
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
