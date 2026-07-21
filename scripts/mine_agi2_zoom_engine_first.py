#!/usr/bin/env python3
"""Engine-first zoom Jordan miner — cooperate with peers writing new engines.

Watches llm_llvm_bench/arc/s*.py mtimes. For each new/changed engine, try all
identity-residue tasks (applies → train_replay perfect → licensed pred).
Much faster than residue×all-engines when peers land engines one-by-one.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]


class Timeout(Exception):
    pass


def _alarm(signum: int, frame: Any) -> None:
    raise Timeout()


def try_engine_on_task(
    arc: Path, eng: str, tid: str, task: Dict[str, Any], timeout_s: float = 1.5
) -> Optional[Tuple[Any, int, int]]:
    path = arc / f"{eng}.py"
    if not path.is_file():
        return None
    signal.signal(signal.SIGALRM, _alarm)
    signal.setitimer(signal.ITIMER_REAL, timeout_s)
    try:
        spec = importlib.util.spec_from_file_location(f"ef_{eng}_{tid}", path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "train_replay") or not hasattr(mod, "submission_fragment"):
            return None
        if hasattr(mod, "applies") and not mod.applies(task):
            return None
        replay = mod.train_replay(task)
        if not (isinstance(replay, dict) and replay.get("perfect")):
            return None
        frag = mod.submission_fragment(tid, task)
        if not frag or tid not in frag:
            return None
        preds = frag[tid]
        if len(preds) != len(task["test"]):
            return None
        lic = sum(
            1
            for i, p in enumerate(preds)
            if isinstance(p.get("attempt_1"), list)
            and p["attempt_1"] != task["test"][i]["input"]
        )
        if lic <= 0:
            return None
        return preds, lic, len(task["train"])
    except Exception:
        return None
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


def seal_closed(gdir: Path, tid: str, eng: str, train_n: int, test_n: int) -> None:
    gdir.mkdir(parents=True, exist_ok=True)
    (gdir / f"{tid}.json").write_text(
        json.dumps(
            {
                "task_id": tid,
                "exam": "ARC-AGI-2",
                "language_game_class": "ZOOM_ENGINE_EXACT",
                "status": "CLOSED",
                "last_gate": "LOCKED",
                "train": train_n,
                "test": test_n,
                "engine": eng,
                "module": f"llm_llvm_bench/arc/{eng}.py",
                "observations": [
                    f"Zoom grammar engine {eng}",
                    f"Train demonstration_replay {train_n}/{train_n}",
                ],
                "validator": "demonstration_replay",
                "validator_result": {
                    "accepted": True,
                    "detail": "train_replay_perfect",
                    "train_replay": f"{train_n}/{train_n}",
                    "engine": eng,
                },
                "c4_invariant": eng,
                "sealed_at_utc": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
        + "\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "reports/airgap_agi2_zoom_engine_mine",
    )
    ap.add_argument("--poll-s", type=float, default=25.0)
    ap.add_argument("--max-rounds", type=int, default=40)
    ap.add_argument("--target-licensed", type=int, default=150)
    ap.add_argument("--seed-recent-s", type=float, default=7200.0)
    args = ap.parse_args()
    root = args.root.resolve()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    arc = root / "llm_llvm_bench" / "arc"
    gdir = root / "reports/exam_reinjection/grammar/arc2"
    ch = json.loads(
        (root / "data/arc-prize-2026-agi-2/arc-agi_test_challenges.json").read_text()
    )
    merge_py = root / "scripts/merge_agi2_licensed_airgap.py"

    sub_path = out / "submission.partial.json"
    mine: Dict[str, Any] = (
        json.loads(sub_path.read_text())
        if sub_path.exists() and sub_path.stat().st_size > 2
        else {}
    )
    seen_mtime: Dict[str, float] = {}
    seed_dirty: Set[str] = set()
    now = time.time()
    for p in arc.glob("s*.py"):
        mtime = p.stat().st_mtime
        seen_mtime[p.stem] = mtime
        if now - mtime <= args.seed_recent_s:
            seed_dirty.add(p.stem)

    session_closes: List[str] = []
    print(
        f"START engine_first mine={len(mine)} target={args.target_licensed} "
        f"seed_engines={len(seed_dirty)} tracked={len(seen_mtime)}",
        flush=True,
    )

    for round_i in range(1, args.max_rounds + 1):
        subprocess.run(
            ["python3", str(merge_py), "--root", str(root), "--rebuild-notebook"],
            check=False,
            capture_output=True,
        )
        m = json.load(
            open(
                root
                / "reports/airgap_agi2_test_20260721T175400Z/MERGED_LICENSED_VS_IDENTITY.json"
            )
        )
        lic = int(m["licensed_grids"])
        raw = (root / "harnesses/hle/hle_eval/hle_qwen3.6-35b-a3b.json").read_text()
        hle = len(set(re.findall(r'^    "([^"]+)": \{', raw, re.M)))
        sub_can = json.loads(
            (
                root
                / "reports/airgap_agi2_test_20260721T175400Z/submission.json"
            ).read_text()
        )
        # reload mine (peers may write same dir)
        if sub_path.exists() and sub_path.stat().st_size > 2:
            peer = json.loads(sub_path.read_text())
            mine.update(peer)

        residue = [
            tid
            for tid, preds in sub_can.items()
            if tid in ch
            and tid not in mine
            and preds
            and preds[0].get("attempt_1") == ch[tid]["test"][0]["input"]
        ]
        print(
            f"round={round_i} lic={lic}/259 HLE={hle} residue={len(residue)} "
            f"mine={len(mine)} session_closes={len(session_closes)}",
            flush=True,
        )
        if lic >= args.target_licensed:
            print("HIT_TARGET", flush=True)
            break

        dirty: List[str] = []
        if seed_dirty:
            dirty = sorted(seed_dirty, key=lambda e: -seen_mtime.get(e, 0))
            seed_dirty.clear()
        else:
            for p in arc.glob("s*.py"):
                mtime = p.stat().st_mtime
                prev = seen_mtime.get(p.stem, 0.0)
                if mtime > prev + 0.01:
                    dirty.append(p.stem)
                    seen_mtime[p.stem] = mtime
            dirty.sort(key=lambda e: -seen_mtime.get(e, 0))
        if not dirty:
            print("no_new_engines sleep", flush=True)
            time.sleep(args.poll_s)
            continue

        print(f"dirty_engines={len(dirty)} head={dirty[:8]}", flush=True)
        new = 0
        for eng in dirty:
            if not residue:
                break
            still: List[str] = []
            for tid in residue:
                if tid in mine:
                    continue
                hit = try_engine_on_task(arc, eng, tid, ch[tid])
                if hit:
                    preds, lic_g, train_n = hit
                    mine[tid] = preds
                    seal_closed(gdir, tid, eng, train_n, len(ch[tid]["test"]))
                    session_closes.append(tid)
                    new += 1
                    print(
                        f"CLOSE {tid} eng={eng} lic_grids={lic_g}",
                        flush=True,
                    )
                else:
                    still.append(tid)
            residue = [t for t in still if t not in mine]

        if new:
            sub_path.write_text(json.dumps(mine))
            subprocess.run(
                ["python3", str(merge_py), "--root", str(root), "--rebuild-notebook"],
                check=False,
                capture_output=True,
            )
            m2 = json.load(
                open(
                    root
                    / "reports/airgap_agi2_test_20260721T175400Z/MERGED_LICENSED_VS_IDENTITY.json"
                )
            )
            print(
                f"post_merge lic={m2['licensed_grids']}/259 new={new} mine={len(mine)}",
                flush=True,
            )
        else:
            time.sleep(args.poll_s)

    subprocess.run(
        ["python3", str(merge_py), "--root", str(root), "--rebuild-notebook"],
        check=False,
        capture_output=True,
    )
    m = json.load(
        open(
            root
            / "reports/airgap_agi2_test_20260721T175400Z/MERGED_LICENSED_VS_IDENTITY.json"
        )
    )
    raw = (root / "harnesses/hle/hle_eval/hle_qwen3.6-35b-a3b.json").read_text()
    hle = len(set(re.findall(r'^    "([^"]+)": \{', raw, re.M)))
    sha = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], text=True
    ).strip()
    summary = {
        "licensed": m["licensed_grids"],
        "hle": hle,
        "mine_stored": len(mine),
        "session_closes": session_closes,
        "session_close_n": len(session_closes),
        "sha": sha,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out / "ENGINE_FIRST_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("DONE", json.dumps(summary), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
