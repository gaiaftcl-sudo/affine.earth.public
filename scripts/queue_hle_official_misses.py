#!/usr/bin/env python3
"""Queue official HLE judged misses for Franklin S4 exam reinjection. No tokens."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--limit", type=int, default=64)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    run_dir = Path(args.run_dir)
    misses_path = run_dir / "misses.json"
    if not misses_path.is_file():
        raise SystemExit(f"missing {misses_path}")
    misses = json.loads(misses_path.read_text())[: args.limit]
    # Honor FRANKLIN_AGI_LANGUAGE_GAME_IMPACT.md: Phase B unwired into HLE turns.
    phase_b = None
    phase_b_path = run_dir / "franklin_phase_b_impact.constraint.json"
    if phase_b_path.is_file():
        try:
            phase_b = json.loads(phase_b_path.read_text())
        except json.JSONDecodeError:
            phase_b = None
    out_dir = root / "reports" / "exam_reinjection"
    out_dir.mkdir(parents=True, exist_ok=True)
    queue_path = out_dir / "hle_official_miss_queue.jsonl"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    with queue_path.open("a", encoding="utf-8") as fh:
        for miss in misses:
            row = {
                "track": "hle",
                "task_id": miss.get("id"),
                "source": "official_cais_hle",
                "run_dir": str(run_dir),
                "model_answer": miss.get("model_answer"),
                "correct_answer": miss.get("correct_answer"),
                "confidence": miss.get("confidence"),
                "queued_utc": stamp,
                "s_state": "incomplete",
                "drift_kind": "understanding drift",
                "phase_b_franklin_hle_turn_wired": False
                if phase_b is not None
                else None,
                "phase_b_exam_efficiency_gain_established": False
                if phase_b is not None
                else None,
            }
            fh.write(json.dumps(row) + "\n")
    meta = {
        "kind": "hle_official_miss_queue_append",
        "queued": len(misses),
        "queue_path": str(queue_path.relative_to(root)),
        "stamp_utc": stamp,
        "franklin_phase_b_impact": phase_b,
    }
    (run_dir / "reinject_queue.receipt.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
