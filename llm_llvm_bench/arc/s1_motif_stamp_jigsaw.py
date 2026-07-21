"""S1 motif-stamp jigsaw language game (FoT).

Grammar family owned here:
  motif_stamp_jigsaw (canonical: eval task 4e34c42c)
    S1: majority color is canvas background; remaining cells form 4-connected stamps.
    S2: drop stamps that are exact subarrays of a larger stamp's bbox crop.
    S3: assemble stamps by consistent 2D overlap offsets (min overlap cells = 3);
        maximize total pairwise overlap, then minimize bounding-box area.
    S4: output = assembled collage with background fill in unpainted cells.
    C4: exact collage; licensed only when every training pair replays.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_MIN_OVERLAP = 3
_MAX_NODES = 20_000
_MAX_STAMPS = 6
_MIN_STAMPS = 2


def _majority(grid: Grid) -> int:
    return Counter(cell for row in grid for cell in row).most_common(1)[0][0]


def _comps4(grid: Grid, pred) -> List[Dict[str, Any]]:
    height = len(grid)
    width = len(grid[0])
    seen = [[False] * width for _ in range(height)]
    out: List[Dict[str, Any]] = []
    for r in range(height):
        for c in range(width):
            if not pred(grid[r][c]) or seen[r][c]:
                continue
            queue = deque([(r, c)])
            seen[r][c] = True
            cells: List[Tuple[int, int]] = []
            while queue:
                x, y = queue.popleft()
                cells.append((x, y))
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if (
                        0 <= nx < height
                        and 0 <= ny < width
                        and not seen[nx][ny]
                        and pred(grid[nx][ny])
                    ):
                        seen[nx][ny] = True
                        queue.append((nx, ny))
            rows = [x for x, _ in cells]
            cols = [y for _, y in cells]
            r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
            full = [
                [grid[x][y] for y in range(c0, c1 + 1)] for x in range(r0, r1 + 1)
            ]
            out.append(
                {
                    "full": full,
                    "size": len(cells),
                    "h": r1 - r0 + 1,
                    "w": c1 - c0 + 1,
                }
            )
    return out


def _is_subarray(small: Grid, big: Grid) -> bool:
    sh, sw = len(small), len(small[0])
    bh, bw = len(big), len(big[0])
    if sh > bh or sw > bw:
        return False
    for r in range(bh - sh + 1):
        for c in range(bw - sw + 1):
            if all(
                small[i][j] == big[r + i][c + j]
                for i in range(sh)
                for j in range(sw)
            ):
                return True
    return False


def _filter_stamps(comps: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        stamp
        for stamp in comps
        if not any(
            stamp is not other
            and stamp["size"] < other["size"]
            and _is_subarray(stamp["full"], other["full"])
            for other in comps
        )
    ]


def _compatible_offsets(a: Grid, b: Grid, min_ov: int) -> List[Tuple[int, int, int]]:
    ah, aw = len(a), len(a[0])
    bh, bw = len(b), len(b[0])
    offs: List[Tuple[int, int, int]] = []
    for dy in range(-bh + 1, ah):
        for dx in range(-bw + 1, aw):
            r0 = max(0, dy)
            r1 = min(ah, dy + bh)
            c0 = max(0, dx)
            c1 = min(aw, dx + bw)
            if r0 >= r1 or c0 >= c1:
                continue
            ok = True
            ov = 0
            for r in range(r0, r1):
                for c in range(c0, c1):
                    if a[r][c] == b[r - dy][c - dx]:
                        ov += 1
                    else:
                        ok = False
                        break
                if not ok:
                    break
            if ok and ov >= min_ov:
                offs.append((dy, dx, ov))
    return offs


def _render(stamps: Sequence[Grid], pos: Sequence[Tuple[int, int]], bg: int) -> Optional[Grid]:
    ys: List[int] = []
    xs: List[int] = []
    for i, (y, x) in enumerate(pos):
        ys.extend([y, y + len(stamps[i]) - 1])
        xs.extend([x, x + len(stamps[i][0]) - 1])
    r0, r1, c0, c1 = min(ys), max(ys), min(xs), max(xs)
    height, width = r1 - r0 + 1, c1 - c0 + 1
    canvas: List[List[Optional[int]]] = [[None] * width for _ in range(height)]
    for i, (y, x) in enumerate(pos):
        for r in range(len(stamps[i])):
            for c in range(len(stamps[i][0])):
                rr, cc = y - r0 + r, x - c0 + c
                val = stamps[i][r][c]
                cur = canvas[rr][cc]
                if cur is None:
                    canvas[rr][cc] = val
                elif cur != val:
                    return None
    return [
        [bg if canvas[r][c] is None else int(canvas[r][c]) for c in range(width)]
        for r in range(height)
    ]


def _assemble(stamps: Sequence[Grid], bg: int, min_ov: int = _MIN_OVERLAP) -> Optional[Grid]:
    n = len(stamps)
    if n == 0:
        return None
    if n == 1:
        return [row[:] for row in stamps[0]]
    pair: List[List[List[Tuple[int, int, int]]]] = [
        [[] for _ in range(n)] for _ in range(n)
    ]
    for i in range(n):
        for j in range(n):
            if i != j:
                pair[i][j] = _compatible_offsets(stamps[i], stamps[j], min_ov)

    best_ov = -1
    best_area = 10**9
    best_grid: Optional[Grid] = None
    nodes = 0

    def dfs(
        pos: List[Optional[Tuple[int, int]]],
        placed: set,
        cur_ov: int,
    ) -> None:
        nonlocal best_ov, best_area, best_grid, nodes
        nodes += 1
        if nodes > _MAX_NODES:
            return
        if len(placed) == n:
            placed_pos = [pos[i] for i in range(n)]
            if any(p is None for p in placed_pos):
                return
            grid = _render(stamps, placed_pos, bg)  # type: ignore[arg-type]
            if grid is None:
                return
            area = len(grid) * len(grid[0])
            if cur_ov > best_ov or (cur_ov == best_ov and area < best_area):
                best_ov = cur_ov
                best_area = area
                best_grid = grid
            return

        candidates: List[Tuple[int, Dict[Tuple[int, int], int]]] = []
        for j in range(n):
            if j in placed:
                continue
            opts: Dict[Tuple[int, int], int] = {}
            for i in placed:
                for dy, dx, _ov in pair[i][j]:
                    assert pos[i] is not None
                    y = pos[i][0] + dy  # type: ignore[index]
                    x = pos[i][1] + dx  # type: ignore[index]
                    ok = True
                    add = 0
                    seen = False
                    for ii in placed:
                        assert pos[ii] is not None
                        ddy = y - pos[ii][0]  # type: ignore[index]
                        ddx = x - pos[ii][1]  # type: ignore[index]
                        ah, aw = len(stamps[ii]), len(stamps[ii][0])
                        bh, bw = len(stamps[j]), len(stamps[j][0])
                        rr0 = max(0, ddy)
                        rr1 = min(ah, ddy + bh)
                        cc0 = max(0, ddx)
                        cc1 = min(aw, ddx + bw)
                        if rr0 < rr1 and cc0 < cc1:
                            matched = next(
                                (
                                    pov
                                    for pdy, pdx, pov in pair[ii][j]
                                    if pdy == ddy and pdx == ddx
                                ),
                                None,
                            )
                            if matched is None:
                                ok = False
                                break
                            add += matched
                            seen = True
                    if ok and seen:
                        opts[(y, x)] = max(opts.get((y, x), 0), add)
            if opts:
                candidates.append((j, opts))
        if not candidates:
            return
        candidates.sort(key=lambda item: (len(item[1]), -max(item[1].values())))
        j, opts = candidates[0]
        for (y, x), add in sorted(opts.items(), key=lambda item: -item[1]):
            pos[j] = (y, x)
            placed.add(j)
            dfs(pos, placed, cur_ov + add)
            placed.remove(j)
            pos[j] = None

    start = max(range(n), key=lambda i: len(stamps[i]) * len(stamps[i][0]))
    pos: List[Optional[Tuple[int, int]]] = [None] * n
    pos[start] = (0, 0)
    dfs(pos, {start}, 0)
    return best_grid


def _extract_stamps(grid: Grid) -> Optional[Tuple[int, List[Grid]]]:
    if not grid or not grid[0]:
        return None
    bg = _majority(grid)
    comps = _comps4(grid, lambda value, background=bg: value != background)
    if not (_MIN_STAMPS <= len(comps) <= _MAX_STAMPS + 2):
        return None
    stamps = [c["full"] for c in _filter_stamps(comps)]
    if not (_MIN_STAMPS <= len(stamps) <= _MAX_STAMPS):
        return None
    return bg, stamps


def _plausible_pair(inp: Grid, out: Grid) -> bool:
    extracted = _extract_stamps(inp)
    if extracted is None:
        return False
    _bg, stamps = extracted
    max_h = max(len(s) for s in stamps)
    max_w = max(len(s[0]) for s in stamps)
    if len(out) < max_h or len(out[0]) < max_w:
        return False
    # Collage is not larger than a loose packing of stamp areas.
    stamp_cells = sum(len(s) * len(s[0]) for s in stamps)
    if len(out) * len(out[0]) > stamp_cells * 3:
        return False
    return True


def motif_stamp_jigsaw(grid: Grid) -> Optional[Grid]:
    extracted = _extract_stamps(grid)
    if extracted is None:
        return None
    bg, stamps = extracted
    return _assemble(stamps, bg, _MIN_OVERLAP)


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("motif_stamp_jigsaw", motif_stamp_jigsaw)]


def exact_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    matched: List[Tuple[str, Transform]] = []
    for name, transform in named_candidates(train):
        if not all(_plausible_pair(ex["input"], ex["output"]) for ex in train):
            continue
        if all(transform(example["input"]) == example["output"] for example in train):
            matched.append((name, transform))
    return matched


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    train = task.get("train", [])
    exact = exact_candidates(train)
    if not exact:
        return {
            "engine": "s1_motif_stamp_jigsaw",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_motif_stamp_jigsaw",
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
    "motif_stamp_jigsaw",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
