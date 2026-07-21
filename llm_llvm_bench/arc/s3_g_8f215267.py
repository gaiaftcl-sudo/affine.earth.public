"""Batch FoT engine for eval task 8f215267.

Grammar family owned here:
  g_8f215267 (canonical: eval task 8f215267)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · 8f215267). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_8f215267(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


"""Solver for ARC-AGI task 8f215267.

Pattern:
- Grid has a background color and several rectangular box frames of different colors.
- Small clusters of non-background colors are scattered outside the boxes.
- For each box of color C, count distinct connected components of color C outside all boxes.
- Place that many dots of color C in the middle row of the box's interior,
  at every-other-column positions starting from the right.
- All external clusters are removed in the output.
"""

from collections import Counter, deque


def solve(grid: list[list[int]]) -> list[list[int]]:
    H = len(grid)
    W = len(grid[0])

    # Background = most common color
    bg = Counter(grid[r][c] for r in range(H) for c in range(W)).most_common(1)[0][0]

    # BFS to find connected components of non-background cells
    visited = [[False] * W for _ in range(H)]
    components: list[tuple[int, set[tuple[int, int]]]] = []

    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not visited[r][c]:
                color = grid[r][c]
                queue = deque([(r, c)])
                visited[r][c] = True
                cells: set[tuple[int, int]] = set()
                while queue:
                    cr, cc = queue.popleft()
                    cells.add((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < H and 0 <= nc < W and not visited[nr][nc] and grid[nr][nc] == color:
                            visited[nr][nc] = True
                            queue.append((nr, nc))
                components.append((color, cells))

    # Classify each component as a rectangular frame (box) or a cluster
    boxes: list[tuple[int, int, int, int, int]] = []  # (color, top, bottom, left, right)
    cluster_count: Counter = Counter()

    for color, cells in components:
        min_r = min(r for r, _ in cells)
        max_r = max(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        max_c = max(c for _, c in cells)

        # Build the set of cells expected for a rectangular frame
        expected: set[tuple[int, int]] = set()
        for c2 in range(min_c, max_c + 1):
            expected.add((min_r, c2))
            expected.add((max_r, c2))
        for r2 in range(min_r + 1, max_r):
            expected.add((r2, min_c))
            expected.add((r2, max_c))

        if cells == expected and (max_r - min_r >= 2) and (max_c - min_c >= 2):
            boxes.append((color, min_r, max_r, min_c, max_c))
        else:
            cluster_count[color] += 1

    # Build output: background everywhere, then draw boxes with interior dots
    output = [[bg] * W for _ in range(H)]

    for color, top, bottom, left, right in boxes:
        # Draw frame border
        for c2 in range(left, right + 1):
            output[top][c2] = color
            output[bottom][c2] = color
        for r2 in range(top + 1, bottom):
            output[r2][left] = color
            output[r2][right] = color

        # Interior bounds
        int_left = left + 1
        int_right = right - 1
        int_top = top + 1
        int_bottom = bottom - 1
        int_height = int_bottom - int_top + 1
        mid_row = int_top + int_height // 2

        # Place N dots from the right, every other column
        n_dots = cluster_count.get(color, 0)
        for i in range(n_dots):
            col = int_right - 1 - 2 * i
            if col >= int_left:
                output[mid_row][col] = color

    return output


if __name__ == "__main__":
    import json, pathlib

    task_path = pathlib.Path(__file__).resolve().parent.parent.parent / "dataset" / "tasks" / "8f215267.json"
    with open(task_path) as f:
        task = json.load(f)

    all_pass = True
    for i, pair in enumerate(task["train"]):
        result = solve(pair["input"])
        status = "PASS" if result == pair["output"] else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"Train pair {i}: {status}")

    for i, pair in enumerate(task.get("test", [])):
        if "output" in pair:
            result = solve(pair["input"])
            status = "PASS" if result == pair["output"] else "FAIL"
            if status == "FAIL":
                all_pass = False
            print(f"Test pair {i}: {status}")
        else:
            print(f"Test pair {i}: (no expected output to verify)")

    if all_pass:
        print("\nAll pairs PASSED!")



def _solve(grid: Grid):
    return solve(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_8f215267", g_8f215267)]


def exact_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    out: List[Tuple[str, Transform]] = []
    for name, transform in named_candidates():
        if all(transform(ex["input"]) == ex["output"] for ex in train):
            out.append((name, transform))
    return out


def train_replay(task: Dict[str, Any]) -> Dict[str, Any]:
    train = task.get("train", [])
    exact = exact_candidates(train)
    if not exact:
        return {
            "engine": "s3_g_8f215267",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
            "primary_transform": None,
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s3_g_8f215267",
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
    "g_8f215267",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
