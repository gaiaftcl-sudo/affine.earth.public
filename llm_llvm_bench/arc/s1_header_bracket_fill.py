"""S1 header-bracket fill language game (FoT).

Grammar family owned here:
  header_bracket_fill (canonical: eval task 97d7923e)
    S1: same canvas shape (in-place rewrite).
    S2: row-0 nonzero colors are the frame legend (header), left-to-right.
    S3: a bracket is a vertical F–C+–F stack whose mid cells touch only 0/C/F
        horizontally (no foreign colors).
    S4: for each legend color F pick one bracket:
        - same column as the legend cell if present (longest), else
        - among brackets reachable from the legend cell through 0-cells:
          sole legend → rightmost; first of many → leftmost;
          last of many → rightmost; middle → nearest column.
    C4: recolor mid C cells to F; licensed by full train replay.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _find_brackets(grid: Grid) -> List[Dict[str, int]]:
    height, width = len(grid), len(grid[0])
    brackets: List[Dict[str, int]] = []
    for col in range(width):
        column = [grid[row][col] for row in range(height)]
        nonzero = [(row, column[row]) for row in range(height) if column[row] != 0]
        for i in range(len(nonzero)):
            for j in range(i + 1, len(nonzero)):
                top, frame = nonzero[i]
                bot, frame2 = nonzero[j]
                if frame != frame2:
                    continue
                mid = [column[row] for row in range(top + 1, bot)]
                if not mid:
                    continue
                fill = mid[0]
                if fill == 0 or fill == frame:
                    continue
                if any(value != fill for value in mid):
                    continue
                isolated = True
                for row in range(top + 1, bot):
                    for dcol in (-1, 1):
                        ncol = col + dcol
                        if 0 <= ncol < width and grid[row][ncol] not in (0, fill, frame):
                            isolated = False
                            break
                    if not isolated:
                        break
                if not isolated:
                    continue
                brackets.append(
                    {"F": frame, "C": fill, "col": col, "top": top, "bot": bot}
                )
    return brackets


def _reachable_through_zero(
    grid: Grid, start: Tuple[int, int], goals: Sequence[Tuple[int, int]]
) -> bool:
    height, width = len(grid), len(grid[0])
    goal_set = set(goals)
    if start in goal_set:
        return True
    queue: deque[Tuple[int, int]] = deque()
    seen: set[Tuple[int, int]] = set()
    sr, sc = start
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = sr + dr, sc + dc
        if 0 <= nr < height and 0 <= nc < width:
            if (nr, nc) in goal_set:
                return True
            if grid[nr][nc] == 0:
                queue.append((nr, nc))
                seen.add((nr, nc))
    while queue:
        row, col = queue.popleft()
        if (row, col) in goal_set:
            return True
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = row + dr, col + dc
            if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in seen:
                if grid[nr][nc] == 0:
                    seen.add((nr, nc))
                    queue.append((nr, nc))
                elif (nr, nc) in goal_set:
                    return True
    return False


def header_bracket_fill(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    height, width = len(grid), len(grid[0])
    header: List[int] = []
    header_cols: Dict[int, int] = {}
    for col, value in enumerate(grid[0]):
        if value and value not in header_cols:
            header.append(value)
            header_cols[value] = col
    if not header:
        return None
    brackets = _find_brackets(grid)
    if not brackets:
        return None
    chosen: List[Dict[str, int]] = []
    for index, frame in enumerate(header):
        home = header_cols[frame]
        candidates = [bracket for bracket in brackets if bracket["F"] == frame]
        if not candidates:
            continue
        same_col = [bracket for bracket in candidates if bracket["col"] == home]
        if same_col:
            chosen.append(max(same_col, key=lambda bracket: bracket["bot"] - bracket["top"]))
            continue
        reachable = [
            bracket
            for bracket in candidates
            if _reachable_through_zero(grid, (0, home), [(bracket["top"], bracket["col"])])
        ]
        pool = reachable or candidates
        if len(header) == 1:
            chosen.append(max(pool, key=lambda bracket: bracket["col"]))
        elif index == 0:
            chosen.append(min(pool, key=lambda bracket: bracket["col"]))
        elif index == len(header) - 1:
            chosen.append(max(pool, key=lambda bracket: bracket["col"]))
        else:
            chosen.append(
                min(pool, key=lambda bracket: (abs(bracket["col"] - home), bracket["col"]))
            )
    if not chosen:
        return None
    out: Grid = [list(row) for row in grid]
    for bracket in chosen:
        frame = bracket["F"]
        for row in range(bracket["top"] + 1, bracket["bot"]):
            out[row][bracket["col"]] = frame
    if out == [list(row) for row in grid]:
        return None
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("header_bracket_fill", header_bracket_fill)]


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
            "engine": "s1_header_bracket_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_header_bracket_fill",
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
    "header_bracket_fill",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
