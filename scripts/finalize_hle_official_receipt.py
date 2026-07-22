#!/usr/bin/env python3
"""Finalize official HLE receipt from upstream judged JSON. Never invents Accuracy."""
from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path


def parse_accuracy_from_log(log_text: str) -> dict | None:
    m = re.search(
        r"Accuracy:\s*([0-9.]+)%\s*\+/-\s*([0-9.]+)%\s*\|\s*n\s*=\s*(\d+)",
        log_text,
    )
    if not m:
        return None
    return {
        "accuracy_pct": float(m.group(1)),
        "ci_half_width_pct": float(m.group(2)),
        "n": int(m.group(3)),
    }


def metrics_from_judged(judged: dict, n: int = 2500) -> dict:
    correct = []
    for _k, v in judged.items():
        jr = v.get("judge_response") or {}
        if not jr:
            continue
        correct.append("yes" in str(jr.get("correct", "")).lower())
    acc = round(100 * sum(correct) / n, 2) if n else None
    half = (
        round(1.96 * math.sqrt(acc * (100 - acc) / n), 2)
        if acc is not None and n
        else None
    )
    return {
        "judged_count": len(correct),
        "correct_count": int(sum(correct)),
        "accuracy_pct": acc,
        "ci_half_width_pct": half,
        "n": n,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--judged", default="")
    ap.add_argument("--predictions", default="")
    ap.add_argument("--model", default="")
    ap.add_argument("--judge-model", default="")
    ap.add_argument("--n", type=int, default=2500)
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    judged_path = Path(args.judged) if args.judged else None
    if judged_path is None or not judged_path.exists():
        cands = sorted(run_dir.glob("judged_hle_*.json"))
        judged_path = cands[-1] if cands else None
    if judged_path is None or not judged_path.exists():
        raise SystemExit(f"judged JSON missing under {run_dir}")

    judged = json.loads(judged_path.read_text())
    metrics = metrics_from_judged(judged, n=args.n)
    log_metrics = None
    log_path = run_dir / "harness.log"
    if log_path.exists():
        log_metrics = parse_accuracy_from_log(log_path.read_text(errors="replace"))

    # Prefer log Accuracy when present (upstream dump_metrics); else recompute.
    accuracy = None
    if log_metrics and log_metrics.get("n") == args.n:
        accuracy = log_metrics["accuracy_pct"]
        ci = log_metrics["ci_half_width_pct"]
    else:
        accuracy = metrics["accuracy_pct"]
        ci = metrics["ci_half_width_pct"]

    misses = []
    for qid, row in judged.items():
        jr = row.get("judge_response") or {}
        if not jr:
            continue
        if "yes" not in str(jr.get("correct", "")).lower():
            misses.append(
                {
                    "id": qid,
                    "model_answer": jr.get("model_answer"),
                    "correct_answer": jr.get("correct_answer"),
                    "confidence": jr.get("confidence"),
                }
            )

    notes = [
        "Accuracy = 100 * correct / n with n=full test-set size (CAIS convention).",
        "Judge model recorded for FoT; CAIS default is o3-mini when available.",
        "Never invent Accuracy; value derived from judged JSON / harness.log.",
    ]
    # Honor FRANKLIN_AGI_LANGUAGE_GAME_IMPACT.md: Phase B capacity is unwired
    # into Franklin HLE turns — do not claim exam-efficiency gain from Phase B.
    phase_b = None
    phase_b_path = run_dir / "franklin_phase_b_impact.constraint.json"
    if phase_b_path.exists():
        try:
            phase_b = json.loads(phase_b_path.read_text())
            notes.append(
                "Phase B Franklin HLE turn path unwired; "
                "phase_b_exam_efficiency_gain_established=false."
            )
        except json.JSONDecodeError:
            phase_b = {"error": "constraint_unreadable", "path": str(phase_b_path)}

    receipt = {
        "kind": "hle_official_judged_receipt",
        "dataset": "cais/hle",
        "split": "test",
        "n": args.n,
        "model": args.model or None,
        "judge_model": args.judge_model or None,
        "official_hle_accuracy": accuracy,
        "accuracy_ci_half_width_pct": ci,
        "judged_count": metrics["judged_count"],
        "correct_count": metrics["correct_count"],
        "miss_count": len(misses),
        "judged_path": str(judged_path),
        "predictions_path": args.predictions or None,
        "stamp_utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "franklin_phase_b_impact": phase_b,
        "notes": notes,
    }
    (run_dir / "official_hle_accuracy.receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    (run_dir / "misses.json").write_text(json.dumps(misses, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
