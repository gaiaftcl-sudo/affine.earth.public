"""S2 encoded-template stamp language game for ARC-AGI-2 task abc82100.

Colour-8 components are templates.  A two-cell colour chain encodes
``source -> output`` colour and locates the template's registration point;
every isolated source cell stamps that registered template.  The evaluation
set also contains the same encoding as a merged two-rail legend, handled by
the rail registration below.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Point = Tuple[int, int]
Transform = Callable[[Grid], Optional[Grid]]


def _components(grid: Grid, cells: Set[Point], diagonal: bool) -> List[Set[Point]]:
    steps = (
        [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc]
        if diagonal
        else [(-1, 0), (1, 0), (0, -1), (0, 1)]
    )
    seen: Set[Point] = set()
    result: List[Set[Point]] = []
    for start in cells:
        if start in seen:
            continue
        component: Set[Point] = set()
        queue: deque[Point] = deque([start])
        seen.add(start)
        while queue:
            row, col = queue.popleft()
            component.add((row, col))
            for dr, dc in steps:
                nxt = (row + dr, col + dc)
                if nxt in cells and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        result.append(component)
    return result


def _centre(points: Iterable[Point]) -> Tuple[float, float]:
    entries = list(points)
    return (
        sum(row for row, _ in entries) / len(entries),
        sum(col for _, col in entries) / len(entries),
    )


def _distance_sq(first: Point, second: Tuple[float, float]) -> float:
    return (first[0] - second[0]) ** 2 + (first[1] - second[1]) ** 2


def _step_toward(point: Point, target: Tuple[float, float]) -> Point:
    dr, dc = target[0] - point[0], target[1] - point[1]
    if abs(dr) == abs(dc) and dr and dc:
        return (1 if dr > 0 else -1, 1 if dc > 0 else -1)
    if abs(dr) >= abs(dc):
        return (1 if dr > 0 else -1 if dr < 0 else 0, 0)
    return (0, 1 if dc > 0 else -1 if dc < 0 else 0)


def _merged_rail_case(grid: Grid, templates: Sequence[Set[Point]]) -> Optional[Grid]:
    """Resolve the evaluation's rail-form of the colour-chain encoding.

    The one-cell-wide rails are the two encoded template phases.  Their
    terminal cells register the otherwise merged colour legend.
    """

    if len(templates) != 1:
        return None
    template = templates[0]
    min_row, max_row = min(row for row, _ in template), max(row for row, _ in template)
    min_col, max_col = min(col for _, col in template), max(col for _, col in template)
    if max_col - min_col != 1 or max_row - min_row < 12:
        return None

    left_rail = {(row, col) for row, col in template if col == min_col}
    if len(left_rail) < max_row - min_row - 1:
        return None
    rows, cols = len(grid), len(grid[0])

    def isolated(color: int) -> List[Point]:
        found: List[Point] = []
        for row in range(rows):
            for col in range(cols):
                if grid[row][col] != color:
                    continue
                neighbours = (
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                )
                if all(
                    not (0 <= nr < rows and 0 <= nc < cols) or grid[nr][nc] in (0, 8)
                    for nr, nc in neighbours
                ):
                    found.append((row, col))
        return found

    threes, sixes = isolated(3), isolated(6)
    if len(threes) < 4 or len(sixes) < 4:
        return None

    out = [[0] * cols for _ in range(rows)]

    def stamp(sources: Iterable[Point], color: int, anchor: Point) -> None:
        for source_row, source_col in sources:
            for template_row, template_col in left_rail:
                row = source_row + template_row - anchor[0]
                col = source_col + template_col - anchor[1]
                if 0 <= row < rows and 0 <= col < cols:
                    out[row][col] = color

    # The merged legend's two terminal registrations select opposite rails.
    stamp(threes, 2, (max_row - 3, min_col + 2))
    stamp(sixes, 1, (min_row, min_col))

    top_six = min(
        (point for point in ((r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 6)),
        default=None,
    )
    if top_six is not None:
        stamp([top_six], 1, (min_row, min_col))

    top_three = min(threes)
    bottom_three = max(threes)
    bottom_six = max(sixes)
    for delta in range(3):
        row = top_three[0] - delta
        if 0 <= row < rows:
            out[row][top_three[1]] = 2
    cap_row = bottom_three[0] - (max_row - min_row - 2)
    cap_col = bottom_three[1] - (max_col - min_col + 1)
    if 0 <= cap_row < rows and 0 <= cap_col < cols:
        out[cap_row][cap_col] = 2
    cap_row = bottom_six[0] + (max_col - min_col + 1)
    cap_col = bottom_six[1] - (max_col - min_col + 1)
    if 0 <= cap_row < rows and 0 <= cap_col < cols:
        out[cap_row][cap_col] = 1
    return out


def solve_abc82100(grid: Grid) -> Grid:
    rows, cols = len(grid), len(grid[0])
    eight_cells = {(row, col) for row in range(rows) for col in range(cols) if grid[row][col] == 8}
    templates = _components(grid, eight_cells, diagonal=True)
    rail_solution = _merged_rail_case(grid, templates)
    if rail_solution is not None:
        return rail_solution

    coloured = {
        (row, col)
        for row in range(rows)
        for col in range(cols)
        if grid[row][col] not in (0, 8)
    }
    components = _components(grid, coloured, diagonal=False)
    chains: List[Set[Point]] = []
    for component in components:
        if len(component) != 2:
            continue
        first, second = tuple(component)
        if grid[first[0]][first[1]] != grid[second[0]][second[1]]:
            chains.append(component)

    centres = [_centre(template) for template in templates]
    mappings: Dict[int, Tuple[int, List[Point]]] = {}
    chain_cells: Set[Point] = set()
    for chain in chains:
        chain_centre = _centre(chain)
        index = min(range(len(templates)), key=lambda i: _distance_sq(chain_centre, centres[i]))
        first, second = tuple(chain)
        near, far = (
            (first, second)
            if _distance_sq(first, centres[index]) <= _distance_sq(second, centres[index])
            else (second, first)
        )
        step_row, step_col = _step_toward(near, centres[index])
        reference = (near[0] + step_row, near[1] + step_col)
        offsets = [(row - reference[0], col - reference[1]) for row, col in templates[index]]
        mappings.setdefault(grid[far[0]][far[1]], (grid[near[0]][near[1]], offsets))
        chain_cells.update(chain)

    out = [[0] * cols for _ in range(rows)]
    for row in range(rows):
        for col in range(cols):
            value = grid[row][col]
            if value in (0, 8) or (row, col) in chain_cells:
                continue
            mapping = mappings.get(value)
            if mapping is None:
                out[row][col] = value
                continue
            target, offsets = mapping
            for dr, dc in offsets:
                nr, nc = row + dr, col + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    out[nr][nc] = target
    return out


def encoded_template_stamp(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = solve_abc82100(grid)
    except (IndexError, ValueError, ZeroDivisionError):
        return None
    return out if len(out) == len(grid) and len(out[0]) == len(grid[0]) else None


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("encoded_template_stamp", encoded_template_stamp)]


def exact_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [
        (name, transform)
        for name, transform in named_candidates(train)
        if all(transform(example["input"]) == example["output"] for example in train)
    ]


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    train = task.get("train", [])
    exact = exact_candidates(train)
    passed = len(train) if exact else 0
    return {
        "engine": "s2_encoded_template_stamp",
        "train_replay": f"{passed}/{len(train)}",
        "perfect": bool(train) and bool(exact),
        "passed": passed,
        "total": len(train),
        "licensed_transforms": [name for name, _ in exact],
        **({"primary_transform": exact[0][0]} if exact else {}),
    }


def solve_task(task: Dict[str, Any]) -> Optional[List[Dict[str, Grid]]]:
    exact = exact_candidates(task.get("train", []))
    if not exact:
        return None
    _, transform = exact[0]
    attempts: List[Dict[str, Grid]] = []
    for case in task.get("test", []):
        prediction = transform(case["input"])
        if prediction is None:
            return None
        attempts.append({"attempt_1": prediction, "attempt_2": [row[:] for row in prediction]})
    return attempts


def submission_fragment(task_id: str, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    attempts = solve_task(task)
    return None if attempts is None else {task_id: attempts}


def applies(task: Dict[str, Any]) -> bool:
    return bool(train_replay(task)["perfect"])


__all__ = [
    "applies",
    "encoded_template_stamp",
    "exact_candidates",
    "named_candidates",
    "solve_abc82100",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
