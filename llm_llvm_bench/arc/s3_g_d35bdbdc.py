"""Batch FoT engine for eval task d35bdbdc.

Grammar family owned here:
  g_d35bdbdc (canonical: eval task d35bdbdc)
    C4: licensed only on perfect train replay.

Core transform adapted from public train-exact solver
(GitMonsters/SOLVED-540-of-540 · d35bdbdc). Never submits to Kaggle.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def g_d35bdbdc(grid: Grid) -> Optional[Grid]:
    if not grid or not grid[0]:
        return None
    try:
        out = _solve(grid)
    except Exception:
        return None
    if not out or not out[0]:
        return None
    return out


"""Solver for d35bdbdc — Block Pointer Chains with 5-Path Fence

Blocks (3x3 square, cross/plus, or edge-truncated) have border and center colors.
Center color = pointer to another block's border color, forming chains.
The 5-path acts as a fence: its endpoints (degree-1 nodes in 8-connectivity)
determine "anchor" blocks (8-adjacent to endpoints) which are always KEPT.
Anchor position sets the keep/remove parity for the chain.
When chains merge (a block has in-degree > 1), the longer pre-merge chain is kept.
Kept blocks get their center updated to the next block's center in the chain.
Output = zeros + 5-cells + kept blocks (with updated centers)."""
import json
from typing import List


def solve(grid: List[List[int]]) -> List[List[int]]:
    rows, cols = len(grid), len(grid[0])

    # --- Detect blocks ---
    blocks = []
    used = set()

    # 3x3 square blocks
    for r in range(rows - 2):
        for c in range(cols - 2):
            border = grid[r][c]
            if border in (0, 5): continue
            center = grid[r+1][c+1]
            if center in (0, 5): continue
            bcs = [(r,c),(r,c+1),(r,c+2),(r+1,c),(r+1,c+2),
                   (r+2,c),(r+2,c+1),(r+2,c+2)]
            if all(grid[br][bc] == border for br, bc in bcs):
                cells = set((r+dr, c+dc) for dr in range(3) for dc in range(3))
                blocks.append((r+1, c+1, border, center, cells))
                used |= cells

    # Cross/plus-shaped blocks
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if (r, c) in used: continue
            center = grid[r][c]
            if center in (0, 5): continue
            arms = [grid[r-1][c], grid[r+1][c], grid[r][c-1], grid[r][c+1]]
            if len(set(arms)) == 1 and arms[0] not in (0, 5):
                border = arms[0]
                if all(grid[r+dr][c+dc] == 0 for dr in (-1,1) for dc in (-1,1)):
                    cells = {(r-1,c),(r,c-1),(r,c),(r,c+1),(r+1,c)}
                    if not (cells & used):
                        blocks.append((r, c, border, center, cells))
                        used |= cells

    # Bottom-edge blocks (2 rows at grid bottom)
    for c in range(cols - 2):
        r = rows - 2
        if any((r+dr, c+dc) in used for dr in range(2) for dc in range(3)):
            continue
        border = grid[r][c]
        if border in (0, 5): continue
        center = grid[r+1][c+1]
        if center in (0, 5) or center == border: continue
        bcs = [(r,c),(r,c+1),(r,c+2),(r+1,c),(r+1,c+2)]
        if all(grid[br][bc] == border for br, bc in bcs):
            cells = set((r+dr, c+dc) for dr in range(2) for dc in range(3))
            blocks.append((r+1, c+1, border, center, cells))
            used |= cells

    # Chain blocks: only those with border != center participate in pointer chains
    cb = [(r, c, b, ct, cells) for r, c, b, ct, cells in blocks if b != ct]
    b2i = {blk[2]: i for i, blk in enumerate(cb)}

    # In-degree for merge detection
    in_deg = [0] * len(cb)
    for blk in cb:
        if blk[3] in b2i:
            in_deg[b2i[blk[3]]] += 1

    # Build chains from chain starts (in-degree 0)
    starts = [i for i in range(len(cb)) if in_deg[i] == 0]
    chains = []
    for s in starts:
        chain, cur, seen = [], s, set()
        while cur is not None and cur not in seen:
            seen.add(cur); chain.append(cur)
            cur = b2i.get(cb[cur][3])
        chains.append(chain)

    merge_pts = {i for i in range(len(cb)) if in_deg[i] > 1}

    # 5-path endpoints (degree <= 1 in 8-connectivity)
    five = {(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 5}
    endpoints = set()
    for r, c in five:
        deg = sum(1 for dr in range(-1, 2) for dc in range(-1, 2)
                  if (dr or dc) and (r+dr, c+dc) in five)
        if deg <= 1:
            endpoints.add((r, c))

    # Anchor blocks: chain blocks 8-adjacent to any endpoint
    anchors = set()
    for er, ec in endpoints:
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                nr, nc = er + dr, ec + dc
                for i, blk in enumerate(cb):
                    if (nr, nc) in blk[4]:
                        anchors.add(i)

    # --- Determine kept blocks ---
    kept = set()

    def process_chain(chain):
        ap = next((i for i, bi in enumerate(chain) if bi in anchors), 0)
        parity = ap % 2
        for i, bi in enumerate(chain):
            is_term = cb[bi][3] not in b2i
            if is_term and bi not in anchors:
                continue
            if i % 2 == parity:
                kept.add(bi)

    if merge_pts:
        merge_cands = {m: [] for m in merge_pts}
        for chain in chains:
            hit = next((bi for bi in chain if bi in merge_pts), None)
            if hit is not None:
                merge_cands[hit].append(chain[:chain.index(hit)])
            else:
                process_chain(chain)
        for cands in merge_cands.values():
            if cands:
                kept.update(max(cands, key=len))
    else:
        for chain in chains:
            process_chain(chain)

    # --- Build output ---
    out = [[0] * cols for _ in range(rows)]
    for r, c in five:
        out[r][c] = 5
    for bi in kept:
        r, c, border, center, cells = cb[bi]
        for cr, cc in cells:
            out[cr][cc] = grid[cr][cc]
        if center in b2i:
            out[r][c] = cb[b2i[center]][3]

    return out


if __name__ == '__main__':
    import sys
    with open(sys.argv[1]) as f: task = json.load(f)
    for split in ('train', 'test'):
        for i, ex in enumerate(task.get(split, [])):
            result = solve(ex['input'])
            match = result == ex['output']
            print(f"{split.title()} {i}: {'PASS ✓' if match else 'FAIL ✗'}")
            if not match:
                for r in range(len(result)):
                    for c in range(len(result[0])):
                        if result[r][c] != ex['output'][r][c]:
                            print(f"  ({r},{c}): got {result[r][c]} expected {ex['output'][r][c]}")



def _solve(grid: Grid):
    return solve(grid)


def named_candidates() -> Sequence[Tuple[str, Transform]]:
    return [("g_d35bdbdc", g_d35bdbdc)]


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
            "engine": "s3_g_d35bdbdc",
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
        "engine": "s3_g_d35bdbdc",
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
    "g_d35bdbdc",
    "solve_task",
    "submission_fragment",
    "train_replay",
]
