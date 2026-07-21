"""S1 hollow accent-fill language game (FoT).

Grammar family owned here:
  hollow_accent_fill (canonical: eval task 3a25b0d8)
    S1: majority color = background; two large 8-connected fg components —
        one mono hollow frame, one multi-color accent object.
    S2: canvas = clean bbox crop of the mono hollow (component cells only).
    S3: align the accent object (D4) by maximizing mono-color frame overlap
        (tie-break: accents landing in hollow cells); paint non-frame accent
        colors into hollow cells; accents that land on the frame seed adjacent
        hollow cells.
    S4: flood each enclosed hollow (bg component not touching the crop border)
        and fill remaining bg cells with the majority accent seed in that hole.
    C4: exact filled hollow grid; licensed only when every training pair replays.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]


def _majority(grid: Grid) -> int:
    return Counter(value for row in grid for value in row).most_common(1)[0][0]


def _d4(grid: Grid) -> List[Grid]:
    variants: List[Grid] = []
    current = grid
    for _ in range(4):
        variants.append(current)
        variants.append([list(reversed(row)) for row in current])
        current = [list(row) for row in zip(*current[::-1])]
    unique: List[Grid] = []
    seen: Set[Tuple[Tuple[int, ...], ...]] = set()
    for variant in variants:
        key = tuple(tuple(row) for row in variant)
        if key not in seen:
            seen.add(key)
            unique.append(variant)
    return unique


def _components8(grid: Grid, bg: int) -> List[Dict[str, Any]]:
    height = len(grid)
    width = len(grid[0])
    seen = [[False] * width for _ in range(height)]
    deltas = [
        (dr, dc)
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if not (dr == 0 and dc == 0)
    ]
    out: List[Dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == bg or seen[row][col]:
                continue
            queue: deque[Cell] = deque([(row, col)])
            seen[row][col] = True
            cells: List[Cell] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in deltas:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] != bg
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
            clean = [[bg] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
            colors: Set[int] = set()
            for r, c in cells:
                value = grid[r][c]
                clean[r - r0][c - c0] = value
                colors.add(value)
            out.append(
                {
                    "size": len(cells),
                    "ncolors": len(colors),
                    "clean": clean,
                }
            )
    return sorted(out, key=lambda item: -item["size"])


def _align_and_fill(mono: Grid, multi: Grid, bg: int) -> Tuple[Grid, Tuple[int, int]]:
    mono_color = Counter(
        value for row in mono for value in row if value != bg
    ).most_common(1)[0][0]
    height = len(mono)
    width = len(mono[0])
    multi_h = len(multi)
    multi_w = len(multi[0])
    best_local = (-1, -1, 0, 0)
    for dr in range(-multi_h + 1, height):
        for dc in range(-multi_w + 1, width):
            overlap = 0
            paint = 0
            for i in range(multi_h):
                for j in range(multi_w):
                    r, c = dr + i, dc + j
                    if not (0 <= r < height and 0 <= c < width):
                        continue
                    if multi[i][j] == mono_color and mono[r][c] == mono_color:
                        overlap += 1
                    value = multi[i][j]
                    if value != bg and value != mono_color and mono[r][c] == bg:
                        paint += 1
            if (overlap, paint) > best_local[:2]:
                best_local = (overlap, paint, dr, dc)
    overlap, paint, dr, dc = best_local
    canvas = [list(row) for row in mono]
    boundary_seeds: List[Tuple[int, int, int]] = []
    for i in range(multi_h):
        for j in range(multi_w):
            value = multi[i][j]
            if value == bg or value == mono_color:
                continue
            r, c = dr + i, dc + j
            if not (0 <= r < height and 0 <= c < width):
                continue
            if canvas[r][c] == bg:
                canvas[r][c] = value
            elif canvas[r][c] == mono_color:
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and mono[nr][nc] == bg
                    ):
                        boundary_seeds.append((nr, nc, value))
    seen = [[False] * width for _ in range(height)]
    for row in range(height):
        for col in range(width):
            if mono[row][col] != bg or seen[row][col]:
                continue
            queue: deque[Cell] = deque([(row, col)])
            seen[row][col] = True
            cells: List[Cell] = []
            accents: Counter[int] = Counter()
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                if canvas[r][c] != bg and canvas[r][c] != mono_color:
                    accents[canvas[r][c]] += 1
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and mono[nr][nc] == bg
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))
            if any(
                r == 0 or c == 0 or r == height - 1 or c == width - 1
                for r, c in cells
            ):
                continue
            cellset = set(cells)
            for hr, hc, color in boundary_seeds:
                if (hr, hc) in cellset:
                    accents[color] += 1
            if accents:
                fill = accents.most_common(1)[0][0]
                for r, c in cells:
                    if canvas[r][c] == bg:
                        canvas[r][c] = fill
    return canvas, (overlap, paint)


def hollow_accent_fill(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    bg = _majority(grid)
    components = [c for c in _components8(grid, bg) if c["size"] >= 10]
    multis = [c for c in components if c["ncolors"] > 1]
    monos = [c for c in components if c["ncolors"] == 1]
    if len(multis) != 1 or len(monos) != 1:
        return None
    mono = monos[0]["clean"]
    best_score = (-1, -1)
    best_canvas: Optional[Grid] = None
    for multi in _d4(multis[0]["clean"]):
        canvas, score = _align_and_fill(mono, multi, bg)
        if score > best_score:
            best_score = score
            best_canvas = canvas
    return best_canvas


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("hollow_accent_fill", hollow_accent_fill)]


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
            "engine": "s1_hollow_accent_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_hollow_accent_fill",
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
    "hollow_accent_fill",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
