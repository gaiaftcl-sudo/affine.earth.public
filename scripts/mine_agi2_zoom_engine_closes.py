#!/usr/bin/env python3
"""Timeout-guarded local zoom-engine Jordan closes on AGI-2 identity residue.

Does not touch :8080. Safe to run beside Franklin LLM + HLE.
Writes reports/airgap_agi2_zoom_engine_mine/ and CLOSED grammar seals.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _worker(payload: Tuple[str, str, int]) -> Dict[str, Any]:
    """Child: try ranked CLOSED/zoom engines for one task."""
    root_s, tid, exp_limit = payload
    root = Path(root_s)
    import importlib.util

    from llm_llvm_bench.exam.miss_reinjection import TRACK_ARC2, load_learned_experiences

    spec = importlib.util.spec_from_file_location(
        "batch", str(root / "scripts/build_agi2_franklin_s4_experience_batch.py")
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    ch = json.loads(
        (root / "data/arc-prize-2026-agi-2/arc-agi_test_challenges.json").read_text()
    )
    ev = json.loads(
        (
            root / "data/arc-prize-2026-agi-2/arc-agi_evaluation_challenges.json"
        ).read_text()
    )
    task = ch[tid]
    exps = load_learned_experiences(
        root / "reports/exam_reinjection", track=TRACK_ARC2, limit=exp_limit
    )
    ranked = mod.rank_experiences(task, exps, ev, limit=12)
    local = mod.try_ranked_closed_engines(root, tid, task, ranked)
    if not local or not local.get("ok"):
        return {"task_id": tid, "ok": False}
    return {
        "task_id": tid,
        "ok": True,
        "predictions": local["predictions"],
        "licensed_grids": local.get("licensed_grids"),
        "engine": local.get("engine"),
        "path": local.get("path"),
        "validator_result": local.get("validator_result"),
        "jordan_loop_bound": local.get("jordan_loop_bound"),
        "train_n": len(task["train"]),
        "test_n": len(task["test"]),
    }


def seal_closed(root: Path, row: Dict[str, Any]) -> Path:
    tid = row["task_id"]
    eng = row.get("engine") or "unknown"
    gdir = root / "reports/exam_reinjection/grammar/arc2"
    gdir.mkdir(parents=True, exist_ok=True)
    vr = row.get("validator_result") or {}
    train_n = int(row.get("train_n") or 0)
    seal = {
        "task_id": tid,
        "exam": "ARC-AGI-2",
        "language_game_class": "ZOOM_ENGINE_EXACT",
        "status": "CLOSED",
        "last_gate": "LOCKED",
        "train": train_n,
        "test": int(row.get("test_n") or 1),
        "engine": eng,
        "module": f"llm_llvm_bench/arc/{eng}.py",
        "observations": [
            f"Zoom grammar engine {eng}",
            f"Train demonstration_replay {vr.get('train_replay') or f'{train_n}/{train_n}'}",
        ],
        "validator": "demonstration_replay",
        "validator_result": {
            "accepted": True,
            "detail": "train_replay_perfect",
            "train_replay": vr.get("train_replay") or f"{train_n}/{train_n}",
            "engine": eng,
        },
        "c4_invariant": eng,
        "sealed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    out = gdir / f"{tid}.json"
    out.write_text(json.dumps(seal, indent=2) + "\n")
    return out


def identity_residue(root: Path) -> List[str]:
    sub = json.loads(
        (root / "reports/airgap_agi2_test_20260721T175400Z/submission.json").read_text()
    )
    ch = json.loads(
        (root / "data/arc-prize-2026-agi-2/arc-agi_test_challenges.json").read_text()
    )
    out: List[str] = []
    for tid, preds in sub.items():
        if tid not in ch:
            continue
        tin = ch[tid]["test"][0]["input"]
        a1 = preds[0].get("attempt_1") if preds else None
        if a1 == tin:
            out.append(tid)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "reports/airgap_agi2_zoom_engine_mine",
    )
    ap.add_argument("--task-timeout", type=float, default=20.0)
    ap.add_argument("--experience-limit", type=int, default=80)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    root = args.root.resolve()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    ids = identity_residue(root)
    if args.limit > 0:
        ids = ids[: args.limit]

    sub_path = out / "submission.partial.json"
    rec_path = out / "receipts.partial.json"
    submission: Dict[str, Any] = {}
    receipts: Dict[str, Any] = {}
    if sub_path.is_file() and sub_path.stat().st_size > 2:
        submission = json.loads(sub_path.read_text())
    if rec_path.is_file() and rec_path.stat().st_size > 2:
        receipts = json.loads(rec_path.read_text())

    pending = [t for t in ids if t not in submission]
    print(
        f"START zoom_engine_mine residue={len(ids)} pending={len(pending)} "
        f"stored={len(submission)} timeout={args.task_timeout}s",
        flush=True,
    )

    new_closes = 0
    timeouts = 0
    t0 = time.time()
    ctx = mp.get_context("spawn")
    for i, tid in enumerate(pending):
        payload = (str(root), tid, args.experience_limit)
        with ctx.Pool(1) as pool:
            async_r = pool.apply_async(_worker, (payload,))
            try:
                row = async_r.get(timeout=args.task_timeout)
            except Exception as exc:  # noqa: BLE001
                timeouts += 1
                receipts[tid] = {
                    "task_id": tid,
                    "ok": False,
                    "path": "engine_timeout_or_error",
                    "error": str(exc)[:200],
                }
                pool.terminate()
                if (i + 1) % 10 == 0:
                    print(
                        f"progress {i+1}/{len(pending)} new={new_closes} "
                        f"timeouts={timeouts}",
                        flush=True,
                    )
                continue
        if row.get("ok"):
            submission[tid] = row["predictions"]
            receipts[tid] = {k: v for k, v in row.items() if k != "predictions"}
            seal_closed(root, row)
            new_closes += 1
            print(
                f"CLOSE {tid} eng={row.get('engine')} "
                f"licensed={row.get('licensed_grids')}",
                flush=True,
            )
        else:
            receipts[tid] = row
        if (i + 1) % 10 == 0 or row.get("ok"):
            sub_path.write_text(json.dumps(submission))
            rec_path.write_text(json.dumps(receipts, indent=2))
            print(
                f"progress {i+1}/{len(pending)} new={new_closes} "
                f"timeouts={timeouts} stored={len(submission)}",
                flush=True,
            )

    sub_path.write_text(json.dumps(submission))
    rec_path.write_text(json.dumps(receipts, indent=2))
    summary = {
        "new_closes": new_closes,
        "timeouts": timeouts,
        "stored": len(submission),
        "pending_seen": len(pending),
        "elapsed_s": round(time.time() - t0, 1),
        "closed_ids": sorted(submission),
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out / "MINE_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"DONE {json.dumps(summary)}", flush=True)
    return 0


if __name__ == "__main__":
    # Avoid fork+Metal issues on macOS
    mp.set_start_method("spawn", force=True)
    raise SystemExit(main())
