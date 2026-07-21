#!/usr/bin/env python3
"""Build AGI-2 Kaggle test submission via local_hybrid_solver (offline).

Maximizes LICENSED (non-identity) grids toward 259/259.
Identity fillers are recorded as IDENTITY / REINJECT — not claimed as mastery.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

Grid = List[List[int]]


def _copy_grid(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _identity_preds(task: Dict[str, Any]) -> List[Dict[str, Grid]]:
    preds = []
    for case in task["test"]:
        g = _copy_grid(case["input"])
        preds.append({"attempt_1": g, "attempt_2": _copy_grid(g)})
    return preds


def _grid_license_flags(
    task: Dict[str, Any], preds: List[Dict[str, Grid]]
) -> List[Dict[str, Any]]:
    rows = []
    for i, case in enumerate(task["test"]):
        inp = case["input"]
        a1 = preds[i]["attempt_1"]
        a2 = preds[i]["attempt_2"]
        non_id = a1 != inp  # prepare-kaggle gate: attempt_1 != test input
        rows.append(
            {
                "test_index": i,
                "status": "LICENSED" if non_id else "IDENTITY",
                "attempt_1_non_identity": a1 != inp,
                "attempt_2_non_identity": a2 != inp,
            }
        )
    return rows


def _solve_one(payload: Tuple[str, str, Dict[str, Any]]) -> Dict[str, Any]:
    root_s, task_id, task = payload
    root = Path(root_s)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from llm_llvm_bench.arc import local_hybrid_solver as lhs

    t0 = time.time()
    frag, receipt = lhs.solve_task(root, task_id, task)
    elapsed = time.time() - t0
    if frag is None:
        preds = _identity_preds(task)
        receipt = dict(receipt or {})
        receipt["ok"] = False
        receipt["placeholder"] = "identity_unlicensed"
    else:
        preds = frag[task_id]
    flags = _grid_license_flags(task, preds)
    licensed_grids = sum(1 for f in flags if f["status"] == "LICENSED")
    return {
        "task_id": task_id,
        "predictions": preds,
        "receipt": receipt,
        "grid_flags": flags,
        "licensed_grids": licensed_grids,
        "total_grids": len(flags),
        "elapsed_s": elapsed,
        "accepted_engine": (receipt or {}).get("accepted_engine"),
        "hybrid_ok": bool((receipt or {}).get("ok")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=max(2, min(12, (os.cpu_count() or 4) - 2)))
    parser.add_argument("--resume", action="store_true", default=True)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument(
        "--icecuber-timeout",
        "--ice-timeout",
        type=float,
        default=30.0,
        dest="icecuber_timeout",
        help="ARC_ICECUBER_TIMEOUT_S per sample inside hybrid",
    )
    parser.add_argument(
        "--task-ids-file",
        type=Path,
        help="Optional JSON list of task_ids to solve (shard mode)",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    resume = args.resume and not args.no_resume

    os.environ["ARC_ICECUBER_TIMEOUT_S"] = str(args.icecuber_timeout)

    challenges = json.loads(
        (root / "data/arc-prize-2026-agi-2/arc-agi_test_challenges.json").read_text(
            encoding="utf-8"
        )
    )
    ids = sorted(challenges)
    if args.task_ids_file is not None:
        wanted = json.loads(args.task_ids_file.read_text(encoding="utf-8"))
        missing = [t for t in wanted if t not in challenges]
        if missing:
            raise SystemExit(f"unknown task ids in shard file: {missing[:5]}")
        ids = [t for t in ids if t in set(wanted)]
        print(f"SHARD mode tasks={len(ids)} from {args.task_ids_file}", flush=True)
    submission: Dict[str, Any] = {}
    per_task: Dict[str, Any] = {}

    partial_path = out_dir / "submission.partial.json"
    receipt_partial = out_dir / "receipts.partial.json"
    if resume and partial_path.is_file() and receipt_partial.is_file():
        submission = json.loads(partial_path.read_text(encoding="utf-8"))
        per_task = json.loads(receipt_partial.read_text(encoding="utf-8"))
        print(f"RESUME done={len(submission)}/{len(ids)}", flush=True)

    pending = [tid for tid in ids if tid not in submission]
    print(
        f"START pending={len(pending)} workers={args.workers} "
        f"icecuber_timeout={args.icecuber_timeout}s",
        flush=True,
    )
    t0 = time.time()
    payloads = [(str(root), tid, challenges[tid]) for tid in pending]

    def _persist() -> None:
        partial_path.write_text(
            json.dumps(submission, separators=(",", ":")), encoding="utf-8"
        )
        receipt_partial.write_text(json.dumps(per_task, indent=2) + "\n", encoding="utf-8")

    if payloads:
        with ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
            futures = {pool.submit(_solve_one, p): p[1] for p in payloads}
            done = 0
            for fut in as_completed(futures):
                result = fut.result()
                tid = result["task_id"]
                submission[tid] = result["predictions"]
                per_task[tid] = {
                    "task_id": tid,
                    "hybrid_ok": result["hybrid_ok"],
                    "accepted_engine": result["accepted_engine"],
                    "licensed_grids": result["licensed_grids"],
                    "total_grids": result["total_grids"],
                    "elapsed_s": result["elapsed_s"],
                    "grid_flags": result["grid_flags"],
                    "placeholder": (result["receipt"] or {}).get("placeholder"),
                }
                done += 1
                if done % 5 == 0 or done == len(payloads):
                    lic = sum(
                        1
                        for tid2, preds in submission.items()
                        for i, pred in enumerate(preds)
                        if pred["attempt_1"] != challenges[tid2]["test"][i]["input"]
                    )
                    total_g = sum(len(v) for v in submission.values())
                    print(
                        f"progress {len(submission)}/{len(ids)} "
                        f"licensed_grids={lic}/{total_g} "
                        f"elapsed={time.time() - t0:.1f}s",
                        flush=True,
                    )
                    _persist()

    # Ensure full key coverage
    for tid in ids:
        if tid not in submission:
            submission[tid] = _identity_preds(challenges[tid])
            per_task[tid] = {
                "task_id": tid,
                "hybrid_ok": False,
                "accepted_engine": None,
                "licensed_grids": 0,
                "total_grids": len(challenges[tid]["test"]),
                "grid_flags": _grid_license_flags(
                    challenges[tid], submission[tid]
                ),
                "placeholder": "identity_unlicensed",
            }

    (out_dir / "submission.json").write_text(
        json.dumps(submission, separators=(",", ":")), encoding="utf-8"
    )

    licensed_grids = 0
    identity_grids = 0
    licensed_tasks = 0
    identity_task_ids = []
    reinject = []
    for tid in ids:
        flags = per_task[tid]["grid_flags"]
        task_lic = sum(1 for f in flags if f["status"] == "LICENSED")
        task_id_n = sum(1 for f in flags if f["status"] == "IDENTITY")
        licensed_grids += task_lic
        identity_grids += task_id_n
        if task_lic == len(flags) and task_lic > 0:
            licensed_tasks += 1
        if task_id_n:
            identity_task_ids.append(tid)
            reinject.append(
                {
                    "task_id": tid,
                    "identity_grids": task_id_n,
                    "total_grids": len(flags),
                    "accepted_engine": per_task[tid].get("accepted_engine"),
                    "action": "REINJECT",
                    "note": "no train-replay-licensed non-identity fill; private labels absent",
                }
            )

    summary = {
        "kind": "agi2_test_hybrid_licensed_receipt",
        "recorded_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tasks": len(ids),
        "grids": licensed_grids + identity_grids,
        "licensed_grids": licensed_grids,
        "identity_grids": identity_grids,
        "licensed_tasks_full": licensed_tasks,
        "identity_task_ids": identity_task_ids,
        "licensed_pct": round(100.0 * licensed_grids / max(1, licensed_grids + identity_grids), 2),
        "workers": args.workers,
        "icecuber_timeout_s": args.icecuber_timeout,
        "elapsed_s": time.time() - t0,
        "submission_path": str((out_dir / "submission.json").relative_to(root)),
        "gate": "attempt_1 != test_input",
        "reinject": reinject,
        "per_task": per_task,
    }
    (out_dir / "receipts.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "LICENSED_VS_IDENTITY.json").write_text(
        json.dumps(
            {
                "licensed_grids": licensed_grids,
                "identity_grids": identity_grids,
                "total_grids": licensed_grids + identity_grids,
                "licensed_pct": summary["licensed_pct"],
                "identity_task_ids": identity_task_ids,
                "reinject_count": len(reinject),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"DONE licensed={licensed_grids}/{licensed_grids + identity_grids} "
        f"identity={identity_grids} pct={summary['licensed_pct']} "
        f"→ {out_dir / 'submission.json'}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
