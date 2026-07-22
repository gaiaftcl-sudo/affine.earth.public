"""S2 dual-band longest-path corridors (FoT).

Grammar (same_canvas_rewrite):
  One 2×2 block of color 2 and many 2×2 blocks of color 8 sit on zeros.
  Build the rectilinear graph of blocks: an edge exists when two blocks share
  a row-span (horizontal corridor) or col-span (vertical corridor) and the
  intervening cells are zero. From the unique 2-block, take a longest simple
  path in that graph (tie-break: fewer painted corridor cells, then lex node
  order). Paint every path edge's corridor with color 7. Orphan 8-blocks off
  the path stay untouched. Licensed only on perfect train replay.

Canonical close: AGI-2 test task 3490cc26.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]

_SEED = 2
_NODE = 8
_PAINT = 7


def _blocks(g: Grid, color: int) -> List[Dict[str, Any]]:
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    out: List[Dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            if g[r][c] != color or seen[r][c]:
                continue
            cells: List[Tuple[int, int]] = []
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and g[nr][nc] == color:
                        seen[nr][nc] = True
                        q.append((nr, nc))
            rs = [x[0] for x in cells]
            cs = [x[1] for x in cells]
            out.append(
                {
                    "r0": min(rs),
                    "r1": max(rs),
                    "c0": min(cs),
                    "c1": max(cs),
                    "color": color,
                }
            )
    return out


def _link(inp: Grid, a: Dict[str, Any], b: Dict[str, Any]) -> Optional[Tuple[Any, ...]]:
    ar0, ar1, ac0, ac1 = a["r0"], a["r1"], a["c0"], a["c1"]
    br0, br1, bc0, bc1 = b["r0"], b["r1"], b["c0"], b["c1"]
    if ar1 - ar0 != 1 or br1 - br0 != 1:
        return None
    if ar0 == br0 and ar1 == br1:
        if ac1 < bc0:
            cols = range(ac1 + 1, bc0)
            if cols and all(inp[r][c] == 0 for r in (ar0, ar1) for c in cols):
                return ("H", ar0, ac1 + 1, bc0 - 1, bc0 - ac1)
        if bc1 < ac0:
            cols = range(bc1 + 1, ac0)
            if cols and all(inp[r][c] == 0 for r in (ar0, ar1) for c in cols):
                return ("H", ar0, bc1 + 1, ac0 - 1, ac0 - bc1)
    if ac0 == bc0 and ac1 == bc1:
        if ar1 < br0:
            rows = range(ar1 + 1, br0)
            if rows and all(inp[r][c] == 0 for c in (ac0, ac1) for r in rows):
                return ("V", ac0, ar1 + 1, br0 - 1, br0 - ar1)
        if br1 < ar0:
            rows = range(br1 + 1, ar0)
            if rows and all(inp[r][c] == 0 for c in (ac0, ac1) for r in rows):
                return ("V", ac0, br1 + 1, ar0 - 1, ar0 - br1)
    return None


def _paint(out: Grid, link: Tuple[Any, ...], paint: int = _PAINT) -> None:
    if link[0] == "H":
        _, r0, c0, c1, _ = link
        for r in (r0, r0 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = paint
    else:
        _, c0, r0, r1, _ = link
        for c in (c0, c0 + 1):
            for r in range(r0, r1 + 1):
                out[r][c] = paint


def _longest_path_corridors(
    inp: Grid,
    seed: int = _SEED,
    node: int = _NODE,
    paint: int = _PAINT,
) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    seeds = _blocks(inp, seed)
    nodes = _blocks(inp, node)
    if len(seeds) != 1 or not nodes:
        return None
    all_nodes: List[Dict[str, Any]] = [seeds[0]] + nodes
    n = len(all_nodes)
    adj: List[List[Tuple[int, Tuple[Any, ...]]]] = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            lc = _link(inp, all_nodes[i], all_nodes[j])
            if lc is not None:
                adj[i].append((j, lc))
                adj[j].append((i, lc))

    best: Optional[Tuple[int, int, List[int], List[Tuple[Any, ...]]]] = None

    def dfs(u: int, visited: set, path: List[int], links: List[Tuple[Any, ...]], cost: int) -> None:
        nonlocal best
        # Maximize path node count; then minimize corridor cell cost; then lex path.
        key = (len(path), -cost, path)
        if best is None or key > (best[0], best[1], best[2]):
            best = (len(path), -cost, path[:], links[:])
        for v, lc in adj[u]:
            if v in visited:
                continue
            visited.add(v)
            path.append(v)
            links.append(lc)
            dfs(v, visited, path, links, cost + int(lc[-1]))
            path.pop()
            links.pop()
            visited.remove(v)

    dfs(0, {0}, [0], [], 0)
    if best is None or best[0] < 2:
        return None
    out = [row[:] for row in inp]
    for lc in best[3]:
        _paint(out, lc, paint=paint)
    return out


def make_dual_band_longest_path_corridors() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _longest_path_corridors(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("dual_band_longest_path_corridors", make_dual_band_longest_path_corridors())]


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
            "engine": "s2_dual_band_longest_path_corridors",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_dual_band_longest_path_corridors",
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
