#!/usr/bin/env python3
"""Build a 240-task AGI-2 test submission via local_hybrid_solver (offline)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(root))
    from llm_llvm_bench.arc import local_hybrid_solver as lhs

    challenges = json.loads(
        (root / "data/arc-prize-2026-agi-2/arc-agi_test_challenges.json").read_text(
            encoding="utf-8"
        )
    )
    submission = {}
    receipts = []
    t0 = time.time()
    ids = sorted(challenges)
    for i, tid in enumerate(ids, 1):
        frag, receipt = lhs.solve_task(root, tid, challenges[tid])
        if frag is None:
            preds = []
            for case in challenges[tid]["test"]:
                grid = [list(row) for row in case["input"]]
                preds.append(
                    {
                        "attempt_1": grid,
                        "attempt_2": [list(row) for row in grid],
                    }
                )
            submission[tid] = preds
            receipt = dict(receipt or {})
            receipt["placeholder"] = "identity_unlicensed"
        else:
            submission[tid] = frag[tid]
        receipts.append(receipt)
        if i % 5 == 0 or i == len(ids):
            ok = sum(1 for r in receipts if r.get("ok"))
            print(
                f"progress {i}/{len(ids)} ok={ok} elapsed={time.time() - t0:.1f}s",
                flush=True,
            )
            (out_dir / "submission.partial.json").write_text(
                json.dumps(submission, separators=(",", ":")), encoding="utf-8"
            )

    (out_dir / "submission.json").write_text(
        json.dumps(submission, separators=(",", ":")), encoding="utf-8"
    )
    summary = {
        "ok": sum(1 for r in receipts if r.get("ok")),
        "total": len(ids),
        "elapsed_s": time.time() - t0,
        "receipts": receipts,
    }
    (out_dir / "receipts.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"DONE {out_dir / 'submission.json'} ok={summary['ok']}/{summary['total']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
