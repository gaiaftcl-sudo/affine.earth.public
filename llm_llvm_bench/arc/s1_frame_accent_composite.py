"""S1 frame accent composite (FoT).

Grammar (zoom_in_crop):
  Find congruent rectangular frames (uniform non-bg border, accented interior).
  Composite all non-border accents from those frames onto one border canvas.

Canonical close: AGI-2 test task 25e02866.
Licensed only on perfect train replay.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Transform = Callable[[Grid], Optional[Grid]]


def make_frame_accent_composite() -> Transform:
    def transform(inp: Grid) -> Optional[Grid]:
        if not inp or not inp[0]:
            return None
        h0, w0 = len(inp), len(inp[0])
        bg = Counter(c for row in inp for c in row).most_common(1)[0][0]
        frames: List[Tuple[int, int, int, int, int, int, int]] = []
        for r0 in range(h0):
            for c0 in range(w0):
                for fh in range(3, min(12, h0 - r0 + 1)):
                    for fw in range(3, min(12, w0 - c0 + 1)):
                        r1, c1 = r0 + fh - 1, c0 + fw - 1
                        border: List[int] = []
                        for c in range(c0, c1 + 1):
                            border += [inp[r0][c], inp[r1][c]]
                        for r in range(r0 + 1, r1):
                            border += [inp[r][c0], inp[r][c1]]
                        if any(v == bg for v in border):
                            continue
                        if len(set(border)) != 1:
                            continue
                        color = border[0]
                        interior = [
                            inp[r][c]
                            for r in range(r0 + 1, r1)
                            for c in range(c0 + 1, c1)
                        ]
                        if not interior or all(v == color for v in interior):
                            continue
                        if not any(v != bg and v != color for v in interior):
                            continue
                        frames.append((r0, c0, r1, c1, color, fh, fw))
        groups: Dict[Tuple[int, int, int], List[Tuple[int, int, int, int, int, int, int]]] = defaultdict(list)
        for fr in frames:
            groups[(fr[5], fr[6], fr[4])].append(fr)
        best = None
        for key, fs in groups.items():
            uniq = []
            seen = set()
            for fr in fs:
                pos = (fr[0], fr[1], fr[2], fr[3])
                if pos in seen:
                    continue
                seen.add(pos)
                uniq.append(fr)
            if len(uniq) >= 2:
                if best is None or key[0] * key[1] > best[0] * best[1]:
                    best = (key[0], key[1], key[2], uniq)
        if best is None:
            return None
        fh, fw, color, fs = best
        out = [[color] * fw for _ in range(fh)]
        for r0, c0, r1, c1, _, _, _ in fs:
            for r in range(fh):
                for c in range(fw):
                    v = inp[r0 + r][c0 + c]
                    if v != bg and v != color:
                        out[r][c] = v
        for c in range(fw):
            out[0][c] = out[fh - 1][c] = color
        for r in range(fh):
            out[r][0] = out[r][fw - 1] = color
        return out

    return transform


def named_candidates(train: Sequence[Dict[str, Any]]) -> List[Tuple[str, Transform]]:
    return [("frame_accent_composite", make_frame_accent_composite())]


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
            "engine": "s1_frame_accent_composite",
            "train_replay": f"0/{len(train)}",
            "perfect": False,
            "passed": 0,
            "total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    passed = sum(transform(ex["input"]) == ex["output"] for ex in train)
    return {
        "engine": "s1_frame_accent_composite",
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
