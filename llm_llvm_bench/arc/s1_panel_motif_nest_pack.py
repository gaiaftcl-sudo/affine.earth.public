"""S1 panel-motif nest pack language game (FoT).

Grammar family owned here:
  panel_motif_nest_pack (canonical: eval task 8698868d)
    S1: majority color = background; non-bg same-color components are objects.
    S2: two object sizes — larger = panels, smaller = motifs (equal counts).
    S3: pair each panel to the motif whose 4-connected bg-hole component count
        equals the panel's bg cell count (ties → reading-order first).
    S4: solidify panel (bg→panel color), center-stamp motif non-bg cells
        (motif bg→panel color); arrange nested tiles on the panel bbox lattice.
    C4: licensed only when every training pair replays exact.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _majority(grid: Grid) -> int:
    return Counter(cell for row in grid for cell in row).most_common(1)[0][0]


def _components(grid: Grid, bg: int) -> List[Dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen = [[False] * width for _ in range(height)]
    comps: List[Dict[str, Any]] = []
    for r in range(height):
        for c in range(width):
            if seen[r][c] or grid[r][c] == bg:
                continue
            color = grid[r][c]
            queue = deque([(r, c)])
            seen[r][c] = True
            cells: List[Tuple[int, int]] = []
            while queue:
                y, x = queue.popleft()
                cells.append((y, x))
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if (
                        0 <= ny < height
                        and 0 <= nx < width
                        and not seen[ny][nx]
                        and grid[ny][nx] == color
                    ):
                        seen[ny][nx] = True
                        queue.append((ny, nx))
            rows = [y for y, _ in cells]
            cols = [x for _, x in cells]
            r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
            full = [list(row[c0 : c1 + 1]) for row in grid[r0 : r1 + 1]]
            comps.append(
                {
                    "col": color,
                    "bbox": (r0, r1, c0, c1),
                    "h": r1 - r0 + 1,
                    "w": c1 - c0 + 1,
                    "full": full,
                }
            )
    return comps


def _hole_components(full: Grid, bg: int) -> int:
    height, width = len(full), len(full[0])
    seen = [[False] * width for _ in range(height)]
    count = 0
    for r in range(height):
        for c in range(width):
            if full[r][c] != bg or seen[r][c]:
                continue
            count += 1
            queue = deque([(r, c)])
            seen[r][c] = True
            while queue:
                y, x = queue.popleft()
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if (
                        0 <= ny < height
                        and 0 <= nx < width
                        and not seen[ny][nx]
                        and full[ny][nx] == bg
                    ):
                        seen[ny][nx] = True
                        queue.append((ny, nx))
    return count


def _nest(panel: Grid, motif: Grid, bg: int, panel_color: int) -> Optional[Grid]:
    out = [list(row) for row in panel]
    height, width = len(out), len(out[0])
    mh, mw = len(motif), len(motif[0])
    if mh > height or mw > width:
        return None
    for r in range(height):
        for c in range(width):
            if out[r][c] == bg:
                out[r][c] = panel_color
    r0 = (height - mh) // 2
    c0 = (width - mw) // 2
    for i in range(mh):
        for j in range(mw):
            value = motif[i][j]
            out[r0 + i][c0 + j] = value if value != bg else panel_color
    return out


def _arrange(panels: Sequence[Dict[str, Any]], tiles: Sequence[Grid]) -> Optional[Grid]:
    row_keys = sorted({panel["bbox"][0] for panel in panels})
    col_keys = sorted({panel["bbox"][2] for panel in panels})
    index = {
        (panel["bbox"][0], panel["bbox"][2]): i for i, panel in enumerate(panels)
    }
    rows: List[Grid] = []
    for row_key in row_keys:
        row_tiles: List[Grid] = []
        for col_key in col_keys:
            key = (row_key, col_key)
            if key not in index:
                return None
            row_tiles.append(tiles[index[key]])
        height = len(row_tiles[0])
        merged = [
            [cell for tile in row_tiles for cell in tile[r]] for r in range(height)
        ]
        rows.append(merged)
    return [cell for row in rows for cell in row]


def panel_motif_nest_pack(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    bg = _majority(grid)
    comps = _components(grid, bg)
    by_size: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}
    for comp in comps:
        by_size.setdefault((comp["h"], comp["w"]), []).append(comp)
    if len(by_size) < 2:
        return None
    sizes = sorted(by_size, key=lambda hw: (-hw[0] * hw[1], -hw[0], -hw[1]))
    panels = sorted(by_size[sizes[0]], key=lambda c: (c["bbox"][0], c["bbox"][2]))
    motifs = list(by_size[sizes[1]])
    if len(panels) != len(motifs) or len(panels) < 2:
        return None
    used: set[int] = set()
    tiles: List[Grid] = []
    for panel in panels:
        panel_holes = sum(cell == bg for row in panel["full"] for cell in row)
        exact = [
            motif
            for motif in motifs
            if id(motif) not in used
            and _hole_components(motif["full"], bg) == panel_holes
        ]
        if not exact:
            return None
        exact.sort(key=lambda c: (c["bbox"][0], c["bbox"][2]))
        motif = exact[0]
        used.add(id(motif))
        nested = _nest(panel["full"], motif["full"], bg, int(panel["col"]))
        if nested is None:
            return None
        tiles.append(nested)
    return _arrange(panels, tiles)


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("panel_motif_nest_pack", panel_motif_nest_pack)]


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
            "engine": "s1_panel_motif_nest_pack",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_panel_motif_nest_pack",
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
    "panel_motif_nest_pack",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
