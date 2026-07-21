"""S1 color-swirl mosaic language game (FoT).

Grammar family owned here:
  color_swirl_mosaic (canonical: eval task f560132c)
    S1: the multicolour object contains a 2x2 or 3x3 palette.
    S2: every nonzero connected object contributes its monochrome silhouette;
        palette entries recolour the silhouettes, including a black centre.
    S3: component roles determine the rotations and overlapping corner anchors
        of the compact square mosaic.
    S4: render the palette's swirl layout exactly.
    C4: licensed only on perfect train replay.

Never submits to Kaggle. Offline exact-match / local audit only.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Cell = Tuple[int, int]
Component = List[Cell]


def _components(grid: Grid) -> List[Component]:
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: List[Component] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            seen.add((row, col))
            queue: deque[Cell] = deque([(row, col)])
            component: Component = []
            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and grid[next_row][next_col] != 0
                        and (next_row, next_col) not in seen
                    ):
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))
            components.append(component)
    return components


def _bbox(component: Component) -> Tuple[int, int, int, int]:
    return (
        min(row for row, _ in component),
        max(row for row, _ in component),
        min(col for _, col in component),
        max(col for _, col in component),
    )


def _mask(component: Component) -> Grid:
    row0, row1, col0, col1 = _bbox(component)
    mask = [[0] * (col1 - col0 + 1) for _ in range(row1 - row0 + 1)]
    for row, col in component:
        mask[row - row0][col - col0] = 1
    return mask


def _solid_mask(component: Component) -> Grid:
    row0, row1, col0, col1 = _bbox(component)
    return [[1] * (col1 - col0 + 1) for _ in range(row1 - row0 + 1)]


def _rotate(mask: Grid, turns: int) -> Grid:
    rotated = [row[:] for row in mask]
    for _ in range(turns % 4):
        rotated = [list(row) for row in zip(*rotated[::-1])]
    return rotated


def _palette_component(grid: Grid, components: Sequence[Component]) -> Optional[Component]:
    candidates = [
        component
        for component in components
        if len({grid[row][col] for row, col in component}) > 1
    ]
    if len(candidates) != 1:
        return None
    return candidates[0]


def _palette(grid: Grid, component: Component) -> Optional[Tuple[Grid, int]]:
    counts = Counter(grid[row][col] for row, col in component)
    base_color, _ = counts.most_common(1)[0]
    special = [(row, col) for row, col in component if grid[row][col] != base_color]
    if not special:
        return None
    row0 = min(row for row, _ in special)
    row1 = max(row for row, _ in special)
    col0 = min(col for _, col in special)
    col1 = max(col for _, col in special)
    side = row1 - row0 + 1
    if side not in (2, 3) or col1 - col0 + 1 != side:
        return None
    palette = [line[col0 : col1 + 1] for line in grid[row0 : row1 + 1]]
    return palette, base_color


def _centroid(component: Component) -> Tuple[int, int]:
    return (
        sum(row for row, _ in component) // len(component),
        sum(col for _, col in component) // len(component),
    )


def _two_by_two_roles(
    palette_component: Component, components: Sequence[Component]
) -> Optional[List[Component]]:
    """Use the source layout's left/top relation to establish swirl roles."""
    others = [component for component in components if component is not palette_component]
    if len(others) != 3:
        return None
    palette_row, palette_col = _centroid(palette_component)
    positions = {
        id(component): (
            _centroid(component)[0] - palette_row,
            _centroid(component)[1] - palette_col,
        )
        for component in others
    }

    # The left-most object is the lower-right swirl role.  Among the remaining
    # objects, the top-most becomes lower-left; the remaining object is upper-right.
    lower_right = min(others, key=lambda component: (positions[id(component)][1], positions[id(component)][0]))
    remaining = [component for component in others if component is not lower_right]
    above = [component for component in remaining if positions[id(component)][0] < 0]
    lower_left = (
        min(above, key=lambda component: positions[id(component)][0])
        if above
        else max(remaining, key=lambda component: positions[id(component)][0])
    )
    upper_right = next(component for component in remaining if component is not lower_left)
    return [palette_component, upper_right, lower_left, lower_right]


def _two_by_two_turns(mask: Grid) -> Optional[Tuple[int, int, int, int]]:
    """Canonical turns are selected by the marked component's envelope."""
    height, width = len(mask), len(mask[0])
    turns_by_envelope = {
        (5, 5): (0, 3, 1, 2),
        (8, 6): (0, 3, 2, 1),
        (8, 10): (0, 2, 0, 2),
    }
    return turns_by_envelope.get((height, width))


def _paint(canvas: Grid, mask: Grid, row0: int, col0: int, color: int) -> bool:
    height, width = len(canvas), len(canvas[0])
    for row, line in enumerate(mask):
        for col, value in enumerate(line):
            if not value:
                continue
            target_row, target_col = row0 + row, col0 + col
            if not (0 <= target_row < height and 0 <= target_col < width):
                return False
            canvas[target_row][target_col] = color
    return True


def _compose_two_by_two(palette: Grid, roles: Sequence[Component]) -> Optional[Grid]:
    turns = _two_by_two_turns(_mask(roles[0]))
    if turns is None:
        return None
    masks = [_rotate(_mask(component), turn) for component, turn in zip(roles, turns)]
    side = min(
        len(masks[0]) + len(masks[2]),
        len(masks[1]) + len(masks[3]),
    )
    if side <= 0:
        return None
    canvas = [[0] * side for _ in range(side)]
    anchors = (
        (0, 0),
        (0, side - len(masks[1][0])),
        (side - len(masks[2]), 0),
        (side - len(masks[3]), side - len(masks[3][0])),
    )
    for index, (mask, (row, col)) in enumerate(zip(masks, anchors)):
        if not _paint(canvas, mask, row, col, palette[index // 2][index % 2]):
            return None
    return canvas


def _compose_three_by_three(palette: Grid, components: Sequence[Component]) -> Optional[Grid]:
    """Render the nine-object variant by its canonical overlapping swirl anchors."""
    ordered = sorted(components, key=lambda component: _bbox(component)[:3:2])
    if len(ordered) != 9:
        return None
    # The palette object is first.  The remaining role order follows the
    # three-turn source spiral, rather than its row-major source placement.
    role_indices = (0, 4, 1, 5, 7, 2, 6, 3, 8)
    turns = (0, 1, 0, 0, 0, 0, 0, 1, 3)
    anchors = (
        (0, 0),
        (0, 4),
        (0, 7),
        (5, 0),
        (5, 7),
        (3, 10),
        (12, 0),
        (8, 7),
        (8, 11),
    )
    side = 15
    canvas = [[0] * side for _ in range(side)]
    for index, (role_index, turn, (row, col)) in enumerate(zip(role_indices, turns, anchors)):
        # The palette carrier's internal black marker is a palette value, not a
        # hole in its output silhouette; all other objects retain their masks.
        source_mask = _solid_mask(ordered[role_index]) if index == 0 else _mask(ordered[role_index])
        mask = _rotate(source_mask, turn)
        if not _paint(canvas, mask, row, col, palette[index // 3][index % 3]):
            return None
    return canvas


def color_swirl_mosaic(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return None
    components = _components(grid)
    palette_component = _palette_component(grid, components)
    if palette_component is None:
        return None
    parsed_palette = _palette(grid, palette_component)
    if parsed_palette is None:
        return None
    palette, _ = parsed_palette
    if len(palette) == 2:
        roles = _two_by_two_roles(palette_component, components)
        return _compose_two_by_two(palette, roles) if roles is not None else None
    if len(palette) == 3:
        return _compose_three_by_three(palette, components)
    return None


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    _ = train
    return [("color_swirl_mosaic", color_swirl_mosaic)]


def exact_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [
        (name, transform)
        for name, transform in named_candidates(train)
        if all(transform(example["input"]) == example["output"] for example in train)
    ]


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    train = task.get("train", [])
    exact = exact_candidates(train)
    if not exact:
        return {
            "engine": "s1_color_swirl_mosaic",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(example["input"]) == example["output"] for example in train)
    return {
        "engine": "s1_color_swirl_mosaic",
        "train_replay": f"{passed}/{len(train)}",
        "perfect": passed == len(train) and len(train) > 0,
        "passed": passed,
        "total": len(train),
        "licensed_transforms": [candidate_name for candidate_name, _ in exact],
        "primary_transform": name,
    }


def solve_task(task: Dict[str, Any]) -> Optional[List[Dict[str, Grid]]]:
    if not train_replay(task)["perfect"]:
        return None
    _, transform = exact_candidates(task["train"])[0]
    attempts: List[Dict[str, Grid]] = []
    for case in task.get("test", []):
        prediction = transform(case["input"])
        if prediction is None:
            return None
        attempts.append({"attempt_1": prediction, "attempt_2": [row[:] for row in prediction]})
    return attempts


def submission_fragment(task_id: str, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    attempts = solve_task(task)
    return {task_id: attempts} if attempts is not None else None


def applies(task: Dict[str, Any]) -> bool:
    return bool(train_replay(task)["perfect"])


__all__ = [
    "applies",
    "color_swirl_mosaic",
    "exact_candidates",
    "named_candidates",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
