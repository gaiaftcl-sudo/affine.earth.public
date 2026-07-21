"""S3 separator ray-fill language game (FoT).

Grammar family owned here:
  separator_ray_fill (canonical: eval task 1ae2feb7)
    S1: same canvas shape (in-place rewrite).
    S2: vertical uniform separator column of one color.
    S3: motifs on the content side ray-fill the empty side.
    S4: fill direction = side with content vs empty; leftward buffer is
        rightward pattern reversed (phase for period fills).
    C4: motif rules licensed by full train replay:
      - single color: period = count; place color every period cells
      - near_count == 1: solid near (suffix singleton)
      - far_count == 1: reverse(collapsed nonzero groups) tiled
      - both counts > 1: B0 templates by near/far count comparison

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def _collapse_nonzero(seq: Sequence[int]) -> List[int]:
    out: List[int] = []
    for value in seq:
        if value == 0:
            continue
        if not out or out[-1] != value:
            out.append(value)
    return out


def find_separator_column(grid: Grid) -> Optional[int]:
    """Vertical column with the most nonzero cells, all one color."""
    if not grid or not grid[0]:
        return None
    height, width = len(grid), len(grid[0])
    best: Optional[int] = None
    best_count = -1
    for col in range(width):
        column = [grid[row][col] for row in range(height)]
        nonzero = [value for value in column if value != 0]
        if nonzero and len(set(nonzero)) == 1 and len(nonzero) > best_count:
            best = col
            best_count = len(nonzero)
    return best


def ray_pattern(source: Sequence[int], length: int) -> List[int]:
    """Rightward ray buffer from a source motif strip."""
    if length <= 0:
        return []
    nonzero = [value for value in source if value != 0]
    if not nonzero:
        return [0] * length
    near = 0
    for value in reversed(source):
        if value != 0:
            near = value
            break
    groups = _collapse_nonzero(source)
    colors = set(nonzero)
    count_near = sum(1 for value in source if value == near)
    if len(colors) == 1:
        period = count_near
        return [near if (index % period) == 0 else 0 for index in range(length)]
    far_colors = [color for color in groups if color != near]
    if not far_colors:
        period = count_near
        return [near if (index % period) == 0 else 0 for index in range(length)]
    far = far_colors[0]
    count_far = sum(1 for value in source if value == far)
    if count_near == 1:
        return [near] * length
    if count_far == 1:
        motif = list(reversed(groups))
        return [motif[index % len(motif)] for index in range(length)]
    if count_near > count_far:
        motif = [near, 0, far, near, far, 0]
    elif count_far > count_near:
        motif = [near, 0, near, far, near, 0]
    else:
        motif = [near, 0, far, near, far, 0]
    return [motif[index % len(motif)] for index in range(length)]


def separator_ray_fill(grid: Grid) -> Optional[Grid]:
    """Ray-fill empty side of a vertical separator from per-row motifs."""
    if not grid or not grid[0]:
        return None
    height, width = len(grid), len(grid[0])
    sep = find_separator_column(grid)
    if sep is None:
        return None
    left_content = sum(
        1 for row in range(height) for col in range(sep) if grid[row][col] != 0
    )
    right_content = sum(
        1
        for row in range(height)
        for col in range(sep + 1, width)
        if grid[row][col] != 0
    )
    if left_content > 0 and right_content == 0:
        fill_right = True
    elif right_content > 0 and left_content == 0:
        fill_right = False
    else:
        # Ambiguous / both sides populated — refuse rather than guess.
        if left_content > 0 and right_content > 0:
            return None
        fill_right = True
    out = [list(row) for row in grid]
    for row in range(height):
        if fill_right:
            source = grid[row][:sep]
            pattern = ray_pattern(source, width - sep - 1)
            for index, value in enumerate(pattern):
                out[row][sep + 1 + index] = value
        else:
            source = grid[row][sep + 1 :]
            pattern = ray_pattern(source, sep)
            placed = list(reversed(pattern))
            for index, value in enumerate(placed):
                out[row][index] = value
    return out


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("separator_ray_fill", separator_ray_fill)]


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
            "engine": "s3_separator_ray_fill",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_separator_ray_fill",
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
        attempts.append(
            {"attempt_1": pred, "attempt_2": [list(row) for row in pred]}
        )
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
    "find_separator_column",
    "named_candidates",
    "ray_pattern",
    "separator_ray_fill",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
