"""S1 panel-motif projection language game (FoT).

Grammar family owned here:
  panel_motif_projection (canonical: eval task 4c7dc4dd)
    S1: four equal hollow rectangular frames (same interior size) on the canvas.
    S2: each frame interior is a motif panel (may be empty / mono / bichrome).
    S3: project one output panel by priority:
        (a) recolor densest bichrome via a disjoint/other-border template
            (desc-freq → asc-freq color map);
        (b) else ortho-connect singleton anchor → ink inside a bichrome panel;
        (c) else XOR all monochrome panels; paint with the rarest panel color.
    C4: exact projected panel; licensed only when every training pair replays.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _find_rects(grid: Grid, max_side: int = 14) -> List[Dict[str, Any]]:
    height = len(grid)
    width = len(grid[0])
    rects: List[Dict[str, Any]] = []
    seen = set()
    for r0 in range(height - 2):
        for c0 in range(width - 2):
            for h in range(3, max_side + 1):
                for w in range(3, max_side + 1):
                    r1, c1 = r0 + h - 1, c0 + w - 1
                    if r1 >= height or c1 >= width:
                        continue
                    top = grid[r0][c0 : c1 + 1]
                    bot = grid[r1][c0 : c1 + 1]
                    if len(set(top)) != 1 or top[0] != bot[0] or len(set(bot)) != 1:
                        continue
                    border = top[0]
                    if border == 0:
                        continue
                    if any(
                        grid[r][c0] != border or grid[r][c1] != border
                        for r in range(r0, r1 + 1)
                    ):
                        continue
                    interior_vals = [
                        grid[r][c]
                        for r in range(r0 + 1, r1)
                        for c in range(c0 + 1, c1)
                    ]
                    if not interior_vals or all(v == border for v in interior_vals):
                        continue
                    if interior_vals.count(0) < 1:
                        continue
                    key = (r0, r1, c0, c1)
                    if key in seen:
                        continue
                    seen.add(key)
                    interior = [
                        [grid[r][c] for c in range(c0 + 1, c1)]
                        for r in range(r0 + 1, r1)
                    ]
                    nz = Counter(v for row in interior for v in row if v)
                    rects.append(
                        {
                            "bbox": key,
                            "bc": border,
                            "interior": interior,
                            "nz": nz,
                            "n": sum(nz.values()),
                        }
                    )
    return rects


def _connect_bichrome(interior: Grid, anchor: int, ink: int) -> Optional[Grid]:
    height = len(interior)
    width = len(interior[0])
    out = [[0] * width for _ in range(height)]
    anchors = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if interior[r][c] == anchor
    ]
    inks = [
        (r, c) for r in range(height) for c in range(width) if interior[r][c] == ink
    ]
    if not anchors or not inks:
        return None
    for r, c in anchors:
        out[r][c] = anchor
    for r, c in inks:
        out[r][c] = ink
    for ar, ac in anchors:
        for ir, ic in inks:
            for c in range(min(ac, ic), max(ac, ic) + 1):
                if out[ar][c] != anchor:
                    out[ar][c] = ink
            for r in range(min(ar, ir), max(ar, ir) + 1):
                if out[r][ic] != anchor:
                    out[r][ic] = ink
    return out


def _recolor(pattern: Dict[str, Any], template: Dict[str, Any]) -> Optional[Grid]:
    pc = sorted(pattern["nz"].keys(), key=lambda c: (-pattern["nz"][c], c))
    tc = sorted(template["nz"].keys(), key=lambda c: (template["nz"][c], c))
    if len(pc) != len(tc):
        return None
    mapping = dict(zip(pc, tc))
    return [[mapping.get(value, 0) for value in row] for row in pattern["interior"]]


def _xor_mono(panels: Sequence[Dict[str, Any]], paint: int) -> Grid:
    height = len(panels[0]["interior"])
    width = len(panels[0]["interior"][0])
    bits = [[0] * width for _ in range(height)]
    for panel in panels:
        for r in range(height):
            for c in range(width):
                if panel["interior"][r][c]:
                    bits[r][c] ^= 1
    return [[paint if bits[r][c] else 0 for c in range(width)] for r in range(height)]


def panel_motif_projection(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    rects = _find_rects(grid)
    by_bc_size: Dict[Tuple[int, int, int], List[Dict[str, Any]]] = defaultdict(list)
    by_size: Dict[Tuple[int, int], List[Dict[str, Any]]] = defaultdict(list)
    for rect in rects:
        ih, iw = len(rect["interior"]), len(rect["interior"][0])
        by_bc_size[(ih, iw, rect["bc"])].append(rect)
        by_size[(ih, iw)].append(rect)
    groups = list(by_bc_size.values()) + list(by_size.values())
    groups.sort(
        key=lambda group: (
            -len(group),
            -(len(group[0]["interior"]) if group else 0),
        )
    )
    for group in groups:
        if len(group) < 2:
            continue
        nonempty = [rect for rect in group if rect["n"] > 0]
        if not nonempty:
            continue
        pattern = max(nonempty, key=lambda rect: rect["n"])
        bichrome = [rect for rect in nonempty if len(rect["nz"]) == 2]
        if len(pattern["nz"]) == 2:
            templates = []
            for template in bichrome:
                if template is pattern:
                    continue
                if template["bc"] != pattern["bc"] or set(template["nz"]).isdisjoint(
                    set(pattern["nz"])
                ):
                    templates.append(template)
            if templates:
                template = min(templates, key=lambda rect: rect["n"])
                if len(template["nz"]) == 2:
                    pred = _recolor(pattern, template)
                    if pred is not None:
                        return pred
        for rect in bichrome:
            singleton = [color for color, count in rect["nz"].items() if count == 1]
            if len(singleton) == 1:
                anchor = singleton[0]
                ink = next(color for color in rect["nz"] if color != anchor)
                pred = _connect_bichrome(rect["interior"], anchor, ink)
                if pred is not None:
                    return pred
        mono = [rect for rect in nonempty if len(rect["nz"]) == 1]
        if len(mono) >= 2:
            colors = [next(iter(rect["nz"])) for rect in mono]
            counts = Counter(colors)
            paint = min(counts.keys(), key=lambda color: (counts[color], color))
            return _xor_mono(mono, paint)
    return None


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("panel_motif_projection", panel_motif_projection)]


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
            "engine": "s1_panel_motif_projection",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_panel_motif_projection",
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
    "panel_motif_projection",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
