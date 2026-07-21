#!/usr/bin/env python3
"""Merge AGI-2 hybrid partials; prefer LICENSED grids; rebuild airgap payload.

No Kaggle submit. Offline only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


def score_submission(
    challenges: Dict[str, Any], submission: Dict[str, Any]
) -> Tuple[int, int, int]:
    licensed = identity = grids = 0
    for tid, preds in submission.items():
        for i, pred in enumerate(preds):
            grids += 1
            if pred["attempt_1"] != challenges[tid]["test"][i]["input"]:
                licensed += 1
            else:
                identity += 1
    return licensed, identity, grids


def prefer_preds(
    challenges: Dict[str, Any],
    a: List[Dict[str, Any]],
    b: List[Dict[str, Any]],
    tid: str,
) -> List[Dict[str, Any]]:
    out = []
    for i, case in enumerate(challenges[tid]["test"]):
        tin = case["input"]
        pa = a[i] if i < len(a) else None
        pb = b[i] if i < len(b) else None
        a_lic = pa is not None and pa["attempt_1"] != tin
        b_lic = pb is not None and pb["attempt_1"] != tin
        if a_lic and not b_lic:
            out.append(pa)
        elif b_lic and not a_lic:
            out.append(pb)
        elif pa is not None:
            out.append(pa)
        else:
            out.append(pb)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--partials",
        nargs="+",
        type=Path,
        required=True,
        help="submission.partial.json / submission.json paths to merge",
    )
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--rebuild-airgap", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    challenges = json.loads(
        (root / "data/arc-prize-2026-agi-2/arc-agi_test_challenges.json").read_text(
            encoding="utf-8"
        )
    )
    merged: Dict[str, Any] = {}
    for path in args.partials:
        if not path.is_file():
            print(f"skip missing {path}", flush=True)
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for tid, preds in payload.items():
            if tid not in challenges:
                continue
            if tid not in merged:
                merged[tid] = preds
            else:
                merged[tid] = prefer_preds(challenges, merged[tid], preds, tid)

    # Fill missing tasks with identity so shape is complete for airgap rebuild
    for tid, task in challenges.items():
        if tid not in merged:
            merged[tid] = [
                {
                    "attempt_1": [list(r) for r in case["input"]],
                    "attempt_2": [list(r) for r in case["input"]],
                }
                for case in task["test"]
            ]

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "submission.json"
    out_path.write_text(json.dumps(merged, separators=(",", ":")), encoding="utf-8")
    licensed, identity, grids = score_submission(challenges, merged)
    sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    receipt = {
        "licensed_grids": licensed,
        "identity_grids": identity,
        "total_grids": grids,
        "tasks": len(merged),
        "sha256": sha,
        "sources": [str(p) for p in args.partials],
        "identity_fill_is_fail_for_100pct": True,
    }
    (out_dir / "MERGE_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"MERGED licensed={licensed}/{grids} identity={identity} sha={sha}",
        flush=True,
    )

    # validate shape
    subprocess.check_call(
        [
            sys.executable,
            str(root / "scripts/validate_arc_prize_submission.py"),
            str(out_path),
            "--challenges",
            str(root / "data/arc-prize-2026-agi-2/arc-agi_test_challenges.json"),
        ]
    )

    if args.rebuild_airgap:
        subprocess.check_call(
            [
                sys.executable,
                str(root / "scripts/build_arc_airgap_kaggle_notebooks.py"),
                "--root",
                str(root),
                "--agi2-platform-json",
                str(out_path),
            ]
        )
        airgap = root / "kaggle/airgap-notebooks/arc-agi-2/payload/submission.json"
        a_lic, a_id, a_g = score_submission(
            challenges, json.loads(airgap.read_text(encoding="utf-8"))
        )
        print(
            f"AIRGAP rebuilt licensed={a_lic}/{a_g} identity={a_id} "
            f"sha={hashlib.sha256(airgap.read_bytes()).hexdigest()}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
