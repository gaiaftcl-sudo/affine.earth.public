"""S1 marker-frame motif extrapolation language game (FoT).

Grammar family owned here:
  marker_frame_motif_extrapolate (canonical: eval task 20a9e565)
    S1: two color-5 corner markers define the exact output frame bbox.
    S2: remaining nonzero cells are a size-progression of self-similar motifs
        (comb / chevron / ladder / ribbon / bracket cascade).
    S3: extrapolate the next motif(s) along the observed spatial AP using the
        family generator; crop the marker frame from the virtual placement.
    C4: exact cropped grid; licensed only when every training pair replays.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

MARKER = 5

UNIT_A = ["..##.", ".####", "##..#"]
UNIT_B = ["#...#", "##.##", ".###."]


def _marker_frame(grid: Grid) -> Optional[Tuple[int, int, int, int]]:
    cells = [
        (row, col)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value == MARKER
    ]
    if len(cells) < 6:
        return None
    return (
        min(row for row, _ in cells),
        max(row for row, _ in cells),
        min(col for _, col in cells),
        max(col for _, col in cells),
    )


def _motif_objects(grid: Grid) -> List[Dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen = [[False] * width for _ in range(height)]
    out: List[Dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] in (0, MARKER) or seen[row][col]:
                continue
            queue = deque([(row, col)])
            seen[row][col] = True
            cells: List[Tuple[int, int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c, grid[r][c]))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] not in (0, MARKER)
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))
            rows = [r for r, _, _ in cells]
            cols = [c for _, c, _ in cells]
            r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
            motif = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
            for r, c, value in cells:
                motif[r - r0][c - c0] = value
            out.append(
                {
                    "r0": r0,
                    "c0": c0,
                    "r1": r1,
                    "c1": c1,
                    "g": motif,
                    "h": r1 - r0 + 1,
                    "w": c1 - c0 + 1,
                }
            )
    return sorted(
        out, key=lambda obj: (obj["h"] * obj["w"], obj["h"], obj["w"], obj["r0"], obj["c0"])
    )


def _crop_to_frame(
    obj_r0: int, obj_c0: int, motif: Grid, frame: Tuple[int, int, int, int]
) -> Grid:
    r0, r1, c0, c1 = frame
    frame_h, frame_w = r1 - r0 + 1, c1 - c0 + 1
    motif_h, motif_w = len(motif), len(motif[0])
    out = [[0] * frame_w for _ in range(frame_h)]
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            local_r, local_c = row - obj_r0, col - obj_c0
            if 0 <= local_r < motif_h and 0 <= local_c < motif_w:
                out[row - r0][col - c0] = motif[local_r][local_c]
    return out


def _make_ladder(height: int, width: int, color: int) -> Grid:
    out: Grid = []
    for row in range(height):
        if row % 2 == 0:
            out.append([color] * width)
        else:
            out.append([color] + [0] * (width - 2) + [color])
    return out


def _make_comb(height: int, width: int, color: int) -> Grid:
    out = [[color] + [0] * (width - 1) for _ in range(height)]
    for row in (height - 3, height - 1):
        if 0 <= row < height:
            out[row] = [color] * width
    return out


def _grow_chevron(prev: Grid, tip: int, orient_left: bool) -> Grid:
    height = len(prev)
    new = [[0, 0] for _ in range(height + 4)]
    for row in range(height):
        new[row + 2] = list(prev[row])
    side = 0 if orient_left else 1
    if new[2][side] == 0:
        new[2][side] = tip
    if new[height + 1][side] == 0:
        new[height + 1][side] = tip
    if orient_left:
        new[0] = [tip, 0]
        new[1] = [tip, tip]
        new[-2] = [tip, tip]
        new[-1] = [tip, 0]
    else:
        new[0] = [0, tip]
        new[1] = [tip, tip]
        new[-2] = [tip, tip]
        new[-1] = [0, tip]
    return new


def _make_ribbon(width: int, color: int, unit: Sequence[str]) -> Grid:
    out: Grid = []
    for unit_row in unit:
        row: List[int] = []
        while len(row) < width:
            for char in unit_row:
                if len(row) >= width:
                    break
                row.append(color if char == "#" else 0)
        out.append(row)
    return out


def _ribbon_unit(motif: Grid) -> Optional[Tuple[Sequence[str], int]]:
    color = next(value for row in motif for value in row if value)
    for unit in (UNIT_A, UNIT_B):
        if _make_ribbon(len(motif[0]), color, unit) == motif:
            return unit, color
    return None


def _make_bracket(level: int, color_a: int, color_b: int) -> Grid:
    height = 2 * (level + 1)
    width = 5 + 4 * level
    out = [[0] * width for _ in range(height)]
    top_c = color_a if level % 2 == 0 else color_b
    bot_c = color_b if level % 2 == 0 else color_a
    top_w = 5
    top_c0 = (width - top_w) // 2
    for col in range(top_w):
        out[0][top_c0 + col] = top_c
    out[1][top_c0] = top_c
    out[1][top_c0 + top_w - 1] = top_c
    for pair in range(1, level + 1):
        color = bot_c if pair % 2 == 1 else top_c
        other = top_c if color == bot_c else bot_c
        row0 = 2 * pair
        left = 2 * (level - pair)
        gap = 4 * pair - 1
        for index, col0 in enumerate((left, left + 3 + gap)):
            for col in range(3):
                out[row0][col0 + col] = color
            if index == 0:
                out[row0 + 1][col0] = color
                out[row0 + 1][col0 + 1] = 0
                out[row0 + 1][col0 + 2] = other
            else:
                out[row0 + 1][col0] = other
                out[row0 + 1][col0 + 1] = 0
                out[row0 + 1][col0 + 2] = color
    return out


def _detect_family(objs: Sequence[Dict[str, Any]]) -> Optional[str]:
    if len(objs) < 2:
        return None
    widths = {obj["w"] for obj in objs}
    heights = {obj["h"] for obj in objs}
    if widths == {2}:
        return "chevron"
    if heights == {3}:
        return "ribbon"
    if widths == {3} and all(
        obj["g"][0] == [obj["g"][0][0]] * 3
        and (obj["h"] < 2 or obj["g"][1][1] == 0)
        for obj in objs
    ):
        return "ladder"
    if all(all(obj["g"][row][0] != 0 for row in range(obj["h"])) for obj in objs):
        if all(objs[i + 1]["w"] == objs[i]["w"] + 1 for i in range(len(objs) - 1)):
            return "comb"
    if all(obj["h"] == 2 * (i + 1) for i, obj in enumerate(objs)) and all(
        obj["w"] == 5 + 4 * i for i, obj in enumerate(objs)
    ):
        return "bracket"
    return None


def _next_delta(values: Sequence[int]) -> int:
    # Alternation needs ≥3 samples; length-2 always matches i%2 vacuously.
    if len(values) >= 3 and all(values[i] == values[i % 2] for i in range(len(values))):
        return values[len(values) % 2]
    if len(values) >= 2 and len(set(values)) > 1:
        return values[-1] + (values[-1] - values[-2])
    return values[-1]


def _primary_color(motif: Grid) -> int:
    return next(value for row in motif for value in row if value)


def _tip_color(motif: Grid) -> int:
    for value in motif[0]:
        if value:
            return value
    return motif[0][1]


def marker_frame_motif_extrapolate(grid: Grid) -> Optional[Grid]:
    frame = _marker_frame(grid)
    if frame is None:
        return None
    objs = _motif_objects(grid)
    family = _detect_family(objs)
    if family is None:
        return None
    r0, r1, c0, c1 = frame
    frame_h, frame_w = r1 - r0 + 1, c1 - c0 + 1
    row_deltas = [objs[i + 1]["r0"] - objs[i]["r0"] for i in range(len(objs) - 1)]
    col_deltas = [objs[i + 1]["c0"] - objs[i]["c0"] for i in range(len(objs) - 1)]
    next_dr = _next_delta(row_deltas)
    next_dc = _next_delta(col_deltas)

    if family == "ladder":
        palette: List[int] = []
        for obj in objs:
            color = obj["g"][0][0]
            if color not in palette:
                palette.append(color)
        for index, obj in enumerate(objs):
            if _make_ladder(obj["h"], obj["w"], palette[index % 3]) != obj["g"]:
                return None
        cur_r0, cur_c0 = objs[-1]["r0"], objs[-1]["c0"]
        for step in range(1, 8):
            cur_r0 += next_dr
            cur_c0 += next_dc
            height = objs[-1]["h"] + 2 * step
            color_index = (height - objs[0]["h"]) // 2
            color = palette[color_index % 3]
            motif = _make_ladder(height, 3, color)
            if cur_r0 == r0 and cur_c0 == c0 and height == frame_h and 3 == frame_w:
                return motif
            cropped = _crop_to_frame(cur_r0, cur_c0, motif, frame)
            if (
                cur_r0 <= r0
                and cur_r0 + height - 1 >= r1
                and cur_c0 <= c0
                and cur_c0 + 2 >= c1
                and any(value for row in cropped for value in row)
            ):
                return cropped
        if (frame_h - objs[0]["h"]) % 2 == 0:
            color_index = (frame_h - objs[0]["h"]) // 2
            return _make_ladder(frame_h, frame_w, palette[color_index % 3])
        return None

    if family == "comb":
        colors = [_primary_color(obj["g"]) for obj in objs]
        for obj, color in zip(objs, colors):
            if obj["w"] >= 3 and _make_comb(obj["h"], obj["w"], color) != obj["g"]:
                return None
        palette = []
        for color in colors:
            if color not in palette:
                palette.append(color)
        height_deltas = [objs[i + 1]["h"] - objs[i]["h"] for i in range(len(objs) - 1)]
        width_deltas = [objs[i + 1]["w"] - objs[i]["w"] for i in range(len(objs) - 1)]
        cur_r0 = objs[-1]["r0"] + next_dr
        cur_c0 = objs[-1]["c0"] + next_dc
        height = objs[-1]["h"] + height_deltas[-1]
        width = objs[-1]["w"] + width_deltas[-1]
        color = palette[len(objs) % len(palette)]
        motif = _make_comb(height, width, color)
        return _crop_to_frame(cur_r0, cur_c0, motif, frame)

    if family == "chevron":
        tips = [_tip_color(obj["g"]) for obj in objs]
        palette = []
        for tip in tips:
            if tip not in palette:
                palette.append(tip)
        current = [list(row) for row in objs[0]["g"]]
        for index in range(len(objs) - 1):
            tip = palette[(index + 1) % len(palette)]
            current = _grow_chevron(current, tip, index % 2 == 0)
            if current != objs[index + 1]["g"]:
                return None
        step = len(objs) - 1
        cur_r0, cur_c0 = objs[-1]["r0"], objs[-1]["c0"]
        cropped: Optional[Grid] = None
        for offset in range(1, 6):
            tip = palette[(step + offset) % len(palette)]
            current = _grow_chevron(current, tip, (step + offset - 1) % 2 == 0)
            cur_r0 += next_dr
            cur_c0 += next_dc
            cropped = _crop_to_frame(cur_r0, cur_c0, current, frame)
            if (
                cur_r0 <= r0
                and cur_r0 + len(current) - 1 >= r1
                and cur_c0 <= c0
                and cur_c0 + 1 >= c1
                and any(value for row in cropped for value in row)
            ):
                return cropped
        return cropped

    if family == "ribbon":
        units_colors = []
        for obj in objs:
            parsed = _ribbon_unit(obj["g"])
            if parsed is None:
                return None
            units_colors.append(parsed)
        width_deltas = [objs[i + 1]["w"] - objs[i]["w"] for i in range(len(objs) - 1)]
        next_dw = _next_delta(width_deltas)
        next_dc = _next_delta(col_deltas)
        cur_r0 = objs[-1]["r0"] + next_dr
        cur_c0 = objs[-1]["c0"] + next_dc
        width = objs[-1]["w"] + next_dw
        unit, color = units_colors[len(objs) % 2]
        motif = _make_ribbon(width, color, unit)
        return _crop_to_frame(cur_r0, cur_c0, motif, frame)

    if family == "bracket":
        color_a = _primary_color(objs[0]["g"])
        top_colors = sorted({value for value in objs[1]["g"][0] if value})
        color_b = next(color for color in top_colors if color != color_a)
        if any(_make_bracket(i, color_a, color_b) != obj["g"] for i, obj in enumerate(objs)):
            color_a, color_b = color_b, color_a
            if any(
                _make_bracket(i, color_a, color_b) != obj["g"] for i, obj in enumerate(objs)
            ):
                return None
        motif = _make_bracket(len(objs), color_a, color_b)
        cur_r0 = objs[-1]["r0"] + next_dr
        cur_c0 = objs[-1]["c0"] + next_dc
        if (
            cur_r0 == r0
            and cur_c0 == c0
            and len(motif) == frame_h
            and len(motif[0]) == frame_w
        ):
            return motif
        return _crop_to_frame(cur_r0, cur_c0, motif, frame)

    return None


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("marker_frame_motif_extrapolate", marker_frame_motif_extrapolate)]


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
            "engine": "s1_marker_frame_motif",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_marker_frame_motif",
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
    "marker_frame_motif_extrapolate",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
