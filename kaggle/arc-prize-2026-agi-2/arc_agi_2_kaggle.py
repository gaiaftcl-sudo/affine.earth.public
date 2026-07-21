"""Air-gapped ARC-AGI-2 submission entrypoint for Kaggle."""

import argparse
import json
from collections import Counter
from pathlib import Path


def rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def rotate_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def flip_horizontal(grid):
    return [row[::-1] for row in grid]


def flip_vertical(grid):
    return grid[::-1]


def transpose(grid):
    return [list(row) for row in zip(*grid)]


def anti_transpose(grid):
    return rotate_180(transpose(grid))


def background(grid):
    return Counter(cell for row in grid for cell in row).most_common(1)[0][0]


def crop_foreground(grid):
    bg = background(grid)
    positions = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, cell in enumerate(row)
        if cell != bg
    ]
    if not positions:
        return [list(row) for row in grid]
    rows, columns = zip(*positions)
    return [
        row[min(columns) : max(columns) + 1]
        for row in grid[min(rows) : max(rows) + 1]
    ]


def crop_to_color(grid, color):
    positions = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, cell in enumerate(row)
        if cell == color
    ]
    if not positions:
        return [list(row) for row in grid]
    rows, columns = zip(*positions)
    return [
        row[min(columns) : max(columns) + 1]
        for row in grid[min(rows) : max(rows) + 1]
    ]


def color_components(grid, color):
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == color
    }
    components = []
    while remaining:
        start = remaining.pop()
        component = {start}
        frontier = [start]
        while frontier:
            row, column = frontier.pop()
            for neighbor in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    frontier.append(neighbor)
        components.append(component)
    return components


def crop_component(grid, color, select_largest):
    components = color_components(grid, color)
    if not components:
        return [list(row) for row in grid]
    component = sorted(components, key=len, reverse=select_largest)[0]
    rows, columns = zip(*component)
    return [
        row[min(columns) : max(columns) + 1]
        for row in grid[min(rows) : max(rows) + 1]
    ]


def isolate_color_component(grid, color, select_largest):
    """Extract one same-color object into its bounding box."""
    components = color_components(grid, color)
    if not components:
        return [list(row) for row in grid]
    component = sorted(components, key=len, reverse=select_largest)[0]
    rows, columns = zip(*component)
    top, bottom = min(rows), max(rows)
    left, right = min(columns), max(columns)
    bg = background(grid)
    return [
        [color if (row, column) in component else bg for column in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]


def foreground_components(grid):
    bg = background(grid)
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] != bg
    }
    components = []
    while remaining:
        start = remaining.pop()
        component = {start}
        frontier = [start]
        while frontier:
            row, column = frontier.pop()
            for neighbor in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    frontier.append(neighbor)
        components.append(component)
    return components


def crop_foreground_component(grid, select_largest, isolate):
    components = foreground_components(grid)
    if not components:
        return [list(row) for row in grid]
    component = sorted(components, key=len, reverse=select_largest)[0]
    rows, columns = zip(*component)
    top, bottom = min(rows), max(rows)
    left, right = min(columns), max(columns)
    if not isolate:
        return [row[left : right + 1] for row in grid[top : bottom + 1]]
    bg = background(grid)
    return [
        [grid[row][column] if (row, column) in component else bg
         for column in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]


def recolor_by_training_pairs(train):
    mapping = {}
    for example in train:
        source, target = example["input"], example["output"]
        if len(source) != len(target) or any(
            len(left) != len(right) for left, right in zip(source, target)
        ):
            return None
        for source_row, target_row in zip(source, target):
            for source_cell, target_cell in zip(source_row, target_row):
                if source_cell in mapping and mapping[source_cell] != target_cell:
                    return None
                mapping[source_cell] = target_cell
    return mapping


def recolor(grid, mapping):
    return [[mapping.get(cell, cell) for cell in row] for row in grid]


def compose(first, second):
    return lambda grid: second(first(grid))


def scale_up(grid, row_factor, column_factor):
    return [
        [cell for cell in row for _ in range(column_factor)]
        for row in grid
        for _ in range(row_factor)
    ]


def scale_down_mode(grid, row_factor, column_factor):
    height, width = len(grid), len(grid[0])
    if height % row_factor or width % column_factor:
        return [list(row) for row in grid]
    reduced = []
    for row in range(0, height, row_factor):
        reduced_row = []
        for column in range(0, width, column_factor):
            block = [
                grid[r][c]
                for r in range(row, row + row_factor)
                for c in range(column, column + column_factor)
            ]
            reduced_row.append(Counter(block).most_common(1)[0][0])
        reduced.append(reduced_row)
    return reduced


def gravity(grid, direction):
    bg = background(grid)
    height, width = len(grid), len(grid[0])
    result = [[bg for _ in range(width)] for _ in range(height)]
    if direction in ("up", "down"):
        for column in range(width):
            values = [grid[row][column] for row in range(height) if grid[row][column] != bg]
            if direction == "down":
                values.reverse()
                rows = range(height - 1, height - len(values) - 1, -1)
            else:
                rows = range(len(values))
            for row, value in zip(rows, values):
                result[row][column] = value
        return result
    for row in range(height):
        values = [cell for cell in grid[row] if cell != bg]
        if direction == "right":
            values.reverse()
            columns = range(width - 1, width - len(values) - 1, -1)
        else:
            columns = range(len(values))
        for column, value in zip(columns, values):
            result[row][column] = value
    return result


def tile(grid, row_factor, column_factor):
    return [
        row * column_factor
        for _ in range(row_factor)
        for row in grid
    ]


def remove_uniform_color_lines(grid, color, remove_rows, remove_columns):
    """Remove separator rows and columns composed entirely of one color."""
    result = [list(row) for row in grid]
    if remove_rows:
        result = [row for row in result if any(cell != color for cell in row)]
    if remove_columns and result:
        retained = [
            column
            for column in range(len(result[0]))
            if any(row[column] != color for row in result)
        ]
        result = [[row[column] for column in retained] for row in result]
    return result or [list(row) for row in grid]


def reflect_horizontal_from_left(grid):
    """Complete each row from its left half by reflection."""
    width = len(grid[0])
    midpoint = (width + 1) // 2
    return [row[:midpoint] + row[: width // 2][::-1] for row in grid]


def reflect_horizontal_from_right(grid):
    """Complete each row from its right half by reflection."""
    width = len(grid[0])
    midpoint = width // 2
    return [row[midpoint:][::-1] + row[midpoint:] for row in grid]


def reflect_vertical_from_top(grid):
    """Complete the grid from its top half by reflection."""
    height = len(grid)
    midpoint = (height + 1) // 2
    return grid[:midpoint] + grid[: height // 2][::-1]


def reflect_vertical_from_bottom(grid):
    """Complete the grid from its bottom half by reflection."""
    height = len(grid)
    midpoint = height // 2
    return grid[midpoint:][::-1] + grid[midpoint:]


def fill_symmetric_background(grid, axis):
    """Mirror non-background cells across an axis without erasing evidence."""
    bg = background(grid)
    height, width = len(grid), len(grid[0])
    result = [list(row) for row in grid]
    for row in range(height):
        for column in range(width):
            mirror = (
                (row, width - 1 - column)
                if axis == "horizontal"
                else (height - 1 - row, column)
            )
            source = grid[row][column]
            target = grid[mirror[0]][mirror[1]]
            if source != bg and target == bg:
                result[mirror[0]][mirror[1]] = source
            elif target != bg and source == bg:
                result[row][column] = target
    return result


def fitted_recolor(train, geometric_transform):
    """Learn a color permutation after a shape-preserving geometric rule."""
    mapping = {}
    for example in train:
        source = geometric_transform(example["input"])
        target = example["output"]
        if len(source) != len(target) or any(
            len(left) != len(right) for left, right in zip(source, target)
        ):
            return None
        for source_row, target_row in zip(source, target):
            for source_cell, target_cell in zip(source_row, target_row):
                if source_cell in mapping and mapping[source_cell] != target_cell:
                    return None
                mapping[source_cell] = target_cell
    return mapping


def named_candidates(train):
    transforms = [
        ("identity", lambda grid: [list(row) for row in grid]),
        ("rotate_cw", rotate_cw),
        ("rotate_180", rotate_180),
        ("rotate_ccw", rotate_ccw),
        ("flip_horizontal", flip_horizontal),
        ("flip_vertical", flip_vertical),
        ("transpose", transpose),
        ("anti_transpose", anti_transpose),
        ("crop_foreground", crop_foreground),
        ("gravity_up", lambda grid: gravity(grid, "up")),
        ("gravity_down", lambda grid: gravity(grid, "down")),
        ("gravity_left", lambda grid: gravity(grid, "left")),
        ("gravity_right", lambda grid: gravity(grid, "right")),
        ("reflect_horizontal_from_left", reflect_horizontal_from_left),
        ("reflect_horizontal_from_right", reflect_horizontal_from_right),
        ("reflect_vertical_from_top", reflect_vertical_from_top),
        ("reflect_vertical_from_bottom", reflect_vertical_from_bottom),
        (
            "fill_horizontal_symmetric_background",
            lambda grid: fill_symmetric_background(grid, "horizontal"),
        ),
        (
            "fill_vertical_symmetric_background",
            lambda grid: fill_symmetric_background(grid, "vertical"),
        ),
    ]
    candidates = list(transforms)

    # Object-focused ARC tasks often select a particular color or one extreme
    # connected component.  Each selector is still accepted only after exact
    # replay of the full demonstration set.
    for color in range(10):
        candidates.append(
            (
                f"crop_color_{color}",
                lambda grid, selected=color: crop_to_color(grid, selected),
            )
        )
        candidates.append(
            (
                f"crop_largest_component_{color}",
                lambda grid, selected=color: crop_component(grid, selected, True),
            )
        )
        candidates.append(
            (
                f"crop_smallest_component_{color}",
                lambda grid, selected=color: crop_component(grid, selected, False),
            )
        )
        candidates.append(
            (
                f"isolate_largest_component_{color}",
                lambda grid, selected=color:
                isolate_color_component(grid, selected, True),
            )
        )
        candidates.append(
            (
                f"isolate_smallest_component_{color}",
                lambda grid, selected=color:
                isolate_color_component(grid, selected, False),
            )
        )
        candidates.append(
            (
                f"remove_{color}_uniform_rows",
                lambda grid, selected=color:
                remove_uniform_color_lines(grid, selected, True, False),
            )
        )
        candidates.append(
            (
                f"remove_{color}_uniform_columns",
                lambda grid, selected=color:
                remove_uniform_color_lines(grid, selected, False, True),
            )
        )
        candidates.append(
            (
                f"remove_{color}_uniform_lines",
                lambda grid, selected=color:
                remove_uniform_color_lines(grid, selected, True, True),
            )
        )
    for selection, label in ((True, "largest"), (False, "smallest")):
        candidates.append(
            (
                f"crop_{label}_foreground_component",
                lambda grid, largest=selection:
                crop_foreground_component(grid, largest, False),
            )
        )
        candidates.append(
            (
                f"isolate_{label}_foreground_component",
                lambda grid, largest=selection:
                crop_foreground_component(grid, largest, True),
            )
        )

    # Public ARC baselines rely on a small, replay-gated DSL.  Extend the
    # correspondence stage to object selection and separator removal before
    # fitting a color permutation.  This permits crop → recolor and
    # object-isolation → recolor without relaxing exact replay.
    for name, geometric_transform in list(candidates):
        color_mapping = fitted_recolor(train, geometric_transform)
        if color_mapping is not None:
            candidates.append(
                (
                    f"{name}_then_recolor",
                    lambda grid, transform=geometric_transform, mapping=color_mapping:
                    recolor(transform(grid), mapping),
                )
            )

    # Output dimensions often directly encode a uniform expansion, reduction,
    # or periodic tiling rule.  Parameters are inferred from every training
    # pair and replay remains the licensing gate below.
    dimension_pairs = [
        (len(example["input"]), len(example["input"][0]),
         len(example["output"]), len(example["output"][0]))
        for example in train
    ]
    if dimension_pairs:
        in_rows, in_columns, out_rows, out_columns = dimension_pairs[0]
        if all(
            rows == in_rows and columns == in_columns
            and target_rows == out_rows and target_columns == out_columns
            for rows, columns, target_rows, target_columns in dimension_pairs
        ):
            if out_rows % in_rows == 0 and out_columns % in_columns == 0:
                row_factor, column_factor = out_rows // in_rows, out_columns // in_columns
                if row_factor > 1 or column_factor > 1:
                    candidates.append(
                        (
                            f"scale_up_{row_factor}x{column_factor}",
                            lambda grid, r=row_factor, c=column_factor: scale_up(grid, r, c),
                        )
                    )
                    candidates.append(
                        (
                            f"tile_{row_factor}x{column_factor}",
                            lambda grid, r=row_factor, c=column_factor: tile(grid, r, c),
                        )
                    )
            if in_rows % out_rows == 0 and in_columns % out_columns == 0:
                row_factor, column_factor = in_rows // out_rows, in_columns // out_columns
                if row_factor > 1 or column_factor > 1:
                    candidates.append(
                        (
                            f"scale_down_mode_{row_factor}x{column_factor}",
                            lambda grid, r=row_factor, c=column_factor:
                            scale_down_mode(grid, r, c),
                        )
                    )
    return candidates


def exact_candidates(train):
    matched = []
    for name, transform in named_candidates(train):
        if all(transform(example["input"]) == example["output"] for example in train):
            matched.append((name, transform))
    return matched


def predictions(task, test_input):
    candidates = exact_candidates(task["train"])
    if not candidates:
        candidates = named_candidates(task["train"])
    first_name, first = candidates[0]
    first_grid = first(test_input)
    alternate = next(
        (
            transform
            for name, transform in candidates
            if name != first_name and transform(test_input) != first_grid
        ),
        lambda grid: [list(row) for row in grid],
    )
    return {"attempt_1": first_grid, "attempt_2": alternate(test_input)}


def find_challenges(input_root):
    candidates = sorted(input_root.rglob("arc-agi_test_challenges.json"))
    if len(candidates) != 1:
        raise RuntimeError("Expected exactly one official ARC-AGI-2 test challenge file.")
    return json.loads(candidates[0].read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", default="/kaggle/input")
    parser.add_argument("--output", default="submission.json")
    arguments = parser.parse_args()

    submission = {}
    for task_id, task in find_challenges(Path(arguments.input_root)).items():
        submission[task_id] = [predictions(task, test["input"]) for test in task["test"]]
    Path(arguments.output).write_text(
        json.dumps(submission, separators=(",", ":")), encoding="utf-8"
    )
    print(f"Wrote {arguments.output} for {len(submission)} ARC-AGI-2 tasks.")


if __name__ == "__main__":
    main()
