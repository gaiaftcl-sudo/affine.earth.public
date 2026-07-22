"""S2 host-block nested-frame stamp (FoT).

Grammar (same_canvas_rewrite):
  The majority nonzero color is the host. Other nonzeros form a single seed
  motif embedded in one host block. Peel that motif into nested axis-aligned
  frames (full frames or left-open cups) with integer thicknesses, then stamp
  the same layer stack into every other host|seed block using the seed's
  margins. Licensed only on perfect train replay.

Canonical close: AGI-2 test task 40f6cd08.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]
Layer = Dict[str, Any]


def _extract_layers(pattern: Grid) -> List[Layer]:
    pat = [row[:] for row in pattern]
    layers: List[Layer] = []
    while True:
        h, w = len(pat), len(pat[0])
        if h == 0 or w == 0:
            break
        colors = {v for row in pat for v in row}
        if len(colors) == 1:
            layers.append({"color": next(iter(colors)), "fill": True})
            break

        def top_thick(col: int) -> int:
            t = 0
            while t < h and all(pat[t][c] == col for c in range(w)):
                t += 1
            return t

        def bot_thick(col: int) -> int:
            t = 0
            while t < h and all(pat[h - 1 - t][c] == col for c in range(w)):
                t += 1
            return t

        def left_thick(col: int) -> int:
            t = 0
            while t < w and all(pat[r][t] == col for r in range(h)):
                t += 1
            return t

        def right_thick(col: int) -> int:
            t = 0
            while t < w and all(pat[r][w - 1 - t] == col for r in range(h)):
                t += 1
            return t

        best: Optional[Tuple[str, int, int, int, int, int]] = None
        for col in colors:
            tt, bt, lt, rt = top_thick(col), bot_thick(col), left_thick(col), right_thick(col)
            if tt == h:
                continue
            if lt == 0 and rt >= 1 and tt >= 1 and bt >= 1:
                ok = all(pat[r][w - 1] == col for r in range(h))
                ok = ok and all(v == col for v in pat[0]) and all(v == col for v in pat[-1])
                if ok:
                    best = ("cup", col, tt, bt, 0, rt)
                    break
            if tt >= 1 and lt >= 1 and rt >= 1:
                best = ("frame", col, tt, bt, lt, rt)
                break
        if best is None:
            layers.append(
                {
                    "color": Counter(v for row in pat for v in row).most_common(1)[0][0],
                    "fill": True,
                }
            )
            break
        kind, col, tt, bt, lt, rt = best
        layers.append(
            {
                "color": col,
                "kind": kind,
                "top": tt,
                "bot": bt,
                "left": lt,
                "right": rt,
                "fill": False,
            }
        )
        if kind == "cup":
            if h - tt - bt <= 0 or w - rt <= 0:
                rest = [v for row in pat for v in row if v != col]
                layers.append(
                    {
                        "color": Counter(rest).most_common(1)[0][0] if rest else col,
                        "fill": True,
                    }
                )
                break
            pat = [row[: w - rt] for row in pat[tt : h - bt]]
            continue
        nh, nw = h - tt - bt, w - lt - rt
        if nh <= 0 or nw <= 0:
            break
        pat = [row[lt : w - rt] for row in pat[tt : h - bt]]
    return layers


def _render_layers(layers: List[Layer], H: int, W: int) -> Grid:
    out: Grid = [[0] * W for _ in range(H)]

    def paint(ls: List[Layer], r0: int, r1: int, c0: int, c1: int) -> None:
        if not ls:
            return
        h = r1 - r0 + 1
        w = c1 - c0 + 1
        L = ls[0]
        if L.get("fill") or len(ls) == 1:
            col = int(L["color"])
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    out[r][c] = col
            return
        tt, bt = int(L["top"]), int(L["bot"])
        lt, rt = int(L["left"]), int(L["right"])
        kind = L["kind"]
        col = int(L["color"])
        if kind == "cup":
            while tt + bt >= h and (tt > 0 or bt > 0):
                if tt >= bt and tt > 0:
                    tt -= 1
                elif bt > 0:
                    bt -= 1
                else:
                    break
            while rt >= w and rt > 0:
                rt -= 1
            for c in range(c0, c1 + 1):
                for t in range(tt):
                    out[r0 + t][c] = col
                for t in range(bt):
                    out[r1 - t][c] = col
            for r in range(r0, r1 + 1):
                for t in range(rt):
                    out[r][c1 - t] = col
            ir0, ir1, ic0, ic1 = r0 + tt, r1 - bt, c0, c1 - rt
            if ir0 <= ir1 and ic0 <= ic1:
                paint(ls[1:], ir0, ir1, ic0, ic1)
            return
        while tt + bt >= h and (tt > 0 or bt > 0):
            if tt >= bt and tt > 0:
                tt -= 1
            elif bt > 0:
                bt -= 1
            else:
                break
        while lt + rt >= w and (lt > 0 or rt > 0):
            if lt >= rt and lt > 0:
                lt -= 1
            elif rt > 0:
                rt -= 1
            else:
                break
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r < r0 + tt or r > r1 - bt or c < c0 + lt or c > c1 - rt:
                    out[r][c] = col
        ir0, ir1, ic0, ic1 = r0 + tt, r1 - bt, c0 + lt, c1 - rt
        if ir0 <= ir1 and ic0 <= ic1:
            paint(ls[1:], ir0, ir1, ic0, ic1)

    paint(layers, 0, H - 1, 0, W - 1)
    return out


def _apply(inp: Grid) -> Optional[Grid]:
    if not inp or not inp[0]:
        return None
    h, w = len(inp), len(inp[0])
    cnt = Counter(v for row in inp for v in row if v)
    if not cnt:
        return None
    host = cnt.most_common(1)[0][0]
    seeds = {c for c in cnt if c != host}
    if not seeds:
        return None
    keep = seeds | {host}
    # connected components over keep
    seen = [[False] * w for _ in range(h)]
    blocks: List[Tuple[int, int, int, int, bool]] = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or inp[r][c] not in keep:
                continue
            cells: List[Tuple[int, int]] = []
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and inp[nr][nc] in keep
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))
            rs = [x[0] for x in cells]
            cs = [x[1] for x in cells]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            has_seed = any(inp[rr][cc] in seeds for rr, cc in cells)
            blocks.append((r0, r1, c0, c1, has_seed))
    seed_blocks = [b for b in blocks if b[4]]
    if len(seed_blocks) != 1:
        return None
    r0, r1, c0, c1, _ = seed_blocks[0]
    prs = [
        r
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if inp[r][c] in seeds
    ]
    pcs = [
        c
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if inp[r][c] in seeds
    ]
    if not prs:
        return None
    pr0, pr1, pc0, pc1 = min(prs), max(prs), min(pcs), max(pcs)
    mt, mb = pr0 - r0, r1 - pr1
    ml, mr = pc0 - c0, c1 - pc1
    pattern = [[inp[r][c] for c in range(pc0, pc1 + 1)] for r in range(pr0, pr1 + 1)]
    layers = _extract_layers(pattern)
    if not layers:
        return None
    out = [row[:] for row in inp]
    changed = False
    for R0, R1, C0, C1, has in blocks:
        if has:
            continue
        ir0, ir1 = R0 + mt, R1 - mb
        ic0, ic1 = C0 + ml, C1 - mr
        if ir0 > ir1 or ic0 > ic1:
            continue
        Hh, Ww = ir1 - ir0 + 1, ic1 - ic0 + 1
        scaled = _render_layers(layers, Hh, Ww)
        for i in range(Hh):
            for j in range(Ww):
                if out[ir0 + i][ic0 + j] != scaled[i][j]:
                    out[ir0 + i][ic0 + j] = scaled[i][j]
                    changed = True
    return out if changed else None


def make_host_block_nested_frame_stamp() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        return _apply(inp)

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("host_block_nested_frame_stamp", make_host_block_nested_frame_stamp())]


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
            "engine": "s2_host_block_nested_frame_stamp",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s2_host_block_nested_frame_stamp",
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
