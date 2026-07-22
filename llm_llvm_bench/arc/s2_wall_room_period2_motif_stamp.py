"""S2 wall-room period-2 motif stamp (FoT).

Grammar (same_canvas_rewrite):
  Dominant non-zero color is the wall. Atomic hollow wall rectangles are rooms.
  Group rooms into panels via shared-wall adjacency (connected components).
  Within each panel, cluster room centers into a row×2-col grid. Learn a 2×2
  period-2 color motif from any inked room interiors (non-wall, non-zero) across
  all panels. Stamp each room interior with motif[row%2][col], preserving walls.
  Licensed only on perfect train replay.

Canonical close: AGI-2 test task 2e65ae53.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Room = Tuple[int, int, int, int]


def _wall_color(inp: Grid) -> int:
    return Counter(c for row in inp for c in row if c).most_common(1)[0][0]


def _atomic_rooms(inp: Grid, wall: int) -> List[Room]:
    h, w = len(inp), len(inp[0])
    frames: List[Tuple[int, int, int, int, int]] = []
    for r0 in range(h):
        for r1 in range(r0 + 2, h):
            for c0 in range(w):
                for c1 in range(c0 + 2, w):
                    if any(
                        inp[r0][c] != wall or inp[r1][c] != wall
                        for c in range(c0, c1 + 1)
                    ):
                        continue
                    if any(
                        inp[r][c0] != wall or inp[r][c1] != wall
                        for r in range(r0, r1 + 1)
                    ):
                        continue
                    if any(
                        inp[r][c] == wall
                        for r in range(r0 + 1, r1)
                        for c in range(c0 + 1, c1)
                    ):
                        continue
                    area = (r1 - r0 - 1) * (c1 - c0 - 1)
                    if area > 0:
                        frames.append((area, r0, c0, r1, c1))
    rooms: List[Room] = []
    for area, r0, c0, r1, c1 in frames:
        has_child = any(
            a2 < area
            and r0b >= r0
            and c0b >= c0
            and r1b <= r1
            and c1b <= c1
            and (r0b, c0b, r1b, c1b) != (r0, c0, r1, c1)
            and (r0b > r0 or c0b > c0 or r1b < r1 or c1b < c1)
            for a2, r0b, c0b, r1b, c1b in frames
        )
        if not has_child:
            rooms.append((r0, c0, r1, c1))
    return sorted(set(rooms))


def _room_ink(inp: Grid, room: Room, wall: int) -> Optional[int]:
    r0, c0, r1, c1 = room
    cols = Counter(
        inp[r][c]
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
        if inp[r][c] not in (0, wall)
    )
    return cols.most_common(1)[0][0] if cols else None


def _cluster_1d(vals: Sequence[float], k: int) -> Dict[float, int]:
    uniq = sorted(set(vals))
    if len(uniq) <= k:
        return {v: i for i, v in enumerate(uniq)}
    gaps = sorted(
        ((uniq[i + 1] - uniq[i], i) for i in range(len(uniq) - 1)), reverse=True
    )
    cuts = sorted(g[1] for g in gaps[: k - 1])
    mapping: Dict[float, int] = {}
    ci = 0
    for i, v in enumerate(uniq):
        mapping[v] = ci
        if i in cuts:
            ci += 1
    return mapping


def _rooms_share_wall(a: Room, b: Room) -> bool:
    r0a, c0a, r1a, c1a = a
    r0b, c0b, r1b, c1b = b
    if r1a == r0b or r1b == r0a:
        return not (c1a <= c0b or c1b <= c0a)
    if c1a == c0b or c1b == c0a:
        return not (r1a <= r0b or r1b <= r0a)
    return False


def _split_panels(rooms: Sequence[Room]) -> List[List[Room]]:
    """Connected components of rooms that share a wall edge."""
    room_list = list(rooms)
    n = len(room_list)
    if n == 0:
        return []
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    for i in range(n):
        for j in range(i + 1, n):
            if _rooms_share_wall(room_list[i], room_list[j]):
                union(i, j)
    groups: Dict[int, List[Room]] = defaultdict(list)
    for i, room in enumerate(room_list):
        groups[find(i)].append(room)
    return list(groups.values())


def _grid_index_rooms(panel_rooms: Sequence[Room]) -> Dict[Room, Tuple[int, int]]:
    if not panel_rooms:
        return {}
    cys = [(r[0] + r[2]) / 2 for r in panel_rooms]
    cxs = [(r[1] + r[3]) / 2 for r in panel_rooms]
    n = len(panel_rooms)
    k_row = n // 2 if n % 2 == 0 else max(1, (n + 1) // 2)
    cy_u = sorted(set(cys))
    if len(cy_u) == 1:
        row_map = {cy_u[0]: 0}
    else:
        row_map = _cluster_1d(cy_u, min(k_row, len(cy_u)))
    col_map = _cluster_1d(cxs, 2)
    return {
        room: (row_map[cy], col_map[cx])
        for room, cy, cx in zip(panel_rooms, cys, cxs)
    }


def _wall_room_period2_motif_stamp(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    wall = _wall_color(inp)
    rooms = _atomic_rooms(inp, wall)
    if len(rooms) < 4:
        return None
    room_rc: Dict[Room, Tuple[int, int]] = {}
    for panel in _split_panels(rooms):
        room_rc.update(_grid_index_rooms(panel))
    motif: List[List[Optional[int]]] = [[None, None], [None, None]]
    for room, (ri, ci) in room_rc.items():
        ink = _room_ink(inp, room, wall)
        if ink is None:
            continue
        if ci not in (0, 1):
            return None
        motif[ri % 2][ci] = ink
    if any(motif[r][c] is None for r in (0, 1) for c in (0, 1)):
        return None
    out = [row[:] for row in inp]
    for room, (ri, ci) in room_rc.items():
        color = motif[ri % 2][ci]
        assert color is not None
        r0, c0, r1, c1 = room
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                if out[r][c] != wall:
                    out[r][c] = color
    return out


def make_wall_room_period2_motif_stamp() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _wall_room_period2_motif_stamp(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("wall_room_period2_motif_stamp", make_wall_room_period2_motif_stamp())]


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
            "engine": "s2_wall_room_period2_motif_stamp",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_wall_room_period2_motif_stamp",
        "train_replay": f"{passed}/{len(train)}",
        "perfect": passed == len(train) and len(train) > 0,
        "passed": passed,
        "total": len(train),
        "licensed_transforms": [n for n, _ in exact],
        "primary_transform": name,
    }


def solve_task(task: Dict[str, Any]) -> Optional[List[Dict[str, Grid]]]:
    if not train_replay(task)["perfect"]:
        return None
    _, transform = exact_candidates(task["train"])[0]
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
    "solve_task",
    "submission_fragment",
    "train_replay",
]
