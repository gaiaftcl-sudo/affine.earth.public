"""S2 hinge-5 nearest component pack (FoT).

Grammar (zoom_in_crop):
  Color-5 cells are hinges. Recolor each 5 to the nearest nonzero non-5
  (4-connected BFS). Extract same-color 4-connected components. Order them
  by the leftmost column among cells that were not originally 5. Pack
  left-to-right: place each mask at the x-cursor with maximum orthogonal
  contact to already-placed cells (no overlap). On a contact tie, if the
  component's converted-5 rows average in the top half of the canvas, place
  it as low as possible among tied offsets; otherwise as high as possible.
  Crop to the packed width. Vertically: if the input bottom row contains any
  color other than 0/5, bottom-align the packed block in the original height;
  otherwise top-align. Licensed only on perfect train replay.

Canonical close: AGI-2 test task 234bbc79.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_HINGE = 5


def _nearest_non_hinge(inp: Grid, r: int, c: int) -> int:
    h, w = len(inp), len(inp[0])
    dirs = ((-1, 0), (1, 0), (0, -1), (0, 1))
    q = deque([(r, c)])
    seen = {(r, c)}
    while q:
        y, x = q.popleft()
        for dy, dx in dirs:
            ny, nx = y + dy, x + dx
            if not (0 <= ny < h and 0 <= nx < w) or (ny, nx) in seen:
                continue
            seen.add((ny, nx))
            v = inp[ny][nx]
            if v != 0 and v != _HINGE:
                return v
            q.append((ny, nx))
    return 0


def _overlaps(pack: Grid, mask: Grid, yoff: int, xoff: int) -> bool:
    ph, pw = len(pack), len(pack[0])
    mh, mw = len(mask), len(mask[0])
    for r in range(mh):
        for c in range(mw):
            if mask[r][c] == 0:
                continue
            pr, pc = yoff + r, xoff + c
            if not (0 <= pr < ph and 0 <= pc < pw):
                return True
            if pack[pr][pc] != 0:
                return True
    return False


def _contact(pack: Grid, mask: Grid, yoff: int, xoff: int) -> int:
    ph, pw = len(pack), len(pack[0])
    mh, mw = len(mask), len(mask[0])
    dirs = ((-1, 0), (1, 0), (0, -1), (0, 1))
    n = 0
    for r in range(mh):
        for c in range(mw):
            if mask[r][c] == 0:
                continue
            pr, pc = yoff + r, xoff + c
            for dy, dx in dirs:
                yr, xc = pr + dy, pc + dx
                if not (0 <= yr < ph and 0 <= xc < pw) or pack[yr][xc] == 0:
                    continue
                in_new = (
                    yoff <= yr < yoff + mh
                    and xoff <= xc < xoff + mw
                    and mask[yr - yoff][xc - xoff] != 0
                )
                if not in_new:
                    n += 1
    return n


def _hinge5_nearest_comp_pack(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    converted = [row[:] for row in inp]
    for r in range(h):
        for c in range(w):
            if inp[r][c] == _HINGE:
                converted[r][c] = _nearest_non_hinge(inp, r, c)

    seen = [[False] * w for _ in range(h)]
    dirs = ((-1, 0), (1, 0), (0, -1), (0, 1))
    comps: List[Dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or converted[r][c] == 0:
                continue
            color = converted[r][c]
            cells: List[Tuple[int, int]] = []
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                y, x = q.popleft()
                cells.append((y, x))
                for dy, dx in dirs:
                    ny, nx = y + dy, x + dx
                    if (
                        0 <= ny < h
                        and 0 <= nx < w
                        and not seen[ny][nx]
                        and converted[ny][nx] == color
                    ):
                        seen[ny][nx] = True
                        q.append((ny, nx))
            orig_cols = [x for y, x in cells if inp[y][x] != _HINGE]
            key = min(orig_cols) if orig_cols else min(x for _, x in cells)
            five_rows = [y for y, x in cells if inp[y][x] == _HINGE]
            rs = [y for y, _ in cells]
            cs = [x for _, x in cells]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            mask = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
            for y, x in cells:
                mask[y - r0][x - c0] = color
            comps.append(
                {
                    "key": key,
                    "mask": mask,
                    "five_rows": five_rows,
                    "mh": r1 - r0 + 1,
                    "mw": c1 - c0 + 1,
                }
            )
    if not comps:
        return None
    comps.sort(key=lambda t: t["key"])

    total_w = sum(c["mw"] for c in comps)
    pack = [[0] * total_w for _ in range(h)]
    first = comps[0]
    for r in range(first["mh"]):
        for c in range(first["mw"]):
            pack[r][c] = first["mask"][r][c]
    xoff = first["mw"]

    for comp in comps[1:]:
        mask, mh, mw = comp["mask"], comp["mh"], comp["mw"]
        candidates: List[Tuple[int, int]] = []
        for yoff in range(0, h - mh + 1):
            if _overlaps(pack, mask, yoff, xoff):
                continue
            candidates.append((_contact(pack, mask, yoff, xoff), yoff))
        if not candidates:
            yoff = 0
        else:
            max_ct = max(ct for ct, _ in candidates)
            tied = [y for ct, y in candidates if ct == max_ct]
            if len(tied) == 1:
                yoff = tied[0]
            else:
                fr = comp["five_rows"]
                if fr and (sum(fr) / len(fr)) < (h / 2):
                    yoff = max(tied)
                else:
                    yoff = min(tied)
        for r in range(mh):
            for c in range(mw):
                if mask[r][c]:
                    pack[yoff + r][xoff + c] = mask[r][c]
        xoff += mw

    pack = [row[:xoff] for row in pack]
    used = [i for i in range(h) if any(v != 0 for v in pack[i])]
    if not used:
        return pack
    content = [pack[i][:] for i in range(used[0], used[-1] + 1)]
    ch, cw = len(content), len(content[0])
    out = [[0] * cw for _ in range(h)]
    bottom_has = any(v not in (0, _HINGE) for v in inp[h - 1])
    y0 = h - ch if bottom_has else 0
    for r in range(ch):
        if 0 <= y0 + r < h:
            out[y0 + r] = content[r][:]
    return out


def make_hinge5_nearest_comp_pack() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _hinge5_nearest_comp_pack(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("hinge5_nearest_comp_pack", make_hinge5_nearest_comp_pack())]


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
            "engine": "s2_hinge5_nearest_comp_pack",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_hinge5_nearest_comp_pack",
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
