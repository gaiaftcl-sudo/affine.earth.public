#!/usr/bin/env python3
"""Merge hybrid partials → best licensed AGI-2 submission → rebuild airgap notebook.

No Kaggle submit. Prefers higher licensed-grid count per task_id.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def licensed_count(
    challenges: Dict[str, Any], preds: List[Dict[str, Any]], tid: str
) -> int:
    return sum(
        1
        for i, pred in enumerate(preds)
        if pred["attempt_1"] != challenges[tid]["test"][i]["input"]
    )


def load_submissions(paths: List[Path]) -> List[Tuple[Path, Dict[str, Any]]]:
    out = []
    for path in paths:
        if not path.is_file():
            continue
        out.append((path, json.loads(path.read_text(encoding="utf-8"))))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--canonical-dir",
        type=Path,
        default=None,
        help="Write merged submission.json + receipt here",
    )
    parser.add_argument("--rebuild-notebook", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    challenges = json.loads(
        (root / "data/arc-prize-2026-agi-2/arc-agi_test_challenges.json").read_text(
            encoding="utf-8"
        )
    )
    ids = sorted(challenges)

    sources: List[Path] = []
    for d in sorted((root / "reports").glob("airgap_agi2_test_*")):
        for name in ("submission.json", "submission.partial.json"):
            sources.append(d / name)
    # shard dirs (wave1 + wave2 + nested shard_N)
    for pattern in (
        "airgap_agi2_shard_*",
        "airgap_agi2_wave*_shard_*",
        "airgap_agi2_franklin*_shard_*",
        "airgap_agi2_franklin_s4*",
        "airgap_agi2_franklin_s4_experience*",
        "airgap_agi2_grammar_apply_*",
        "airgap_agi2_grammar_map*",
        "airgap_agi2_grammar*",
        "airgap_agi2_period_*",
        "airgap_agi2_marker_*",
        "airgap_agi2_zoom_grammar_*",
        "airgap_agi2_zoom_engine_*",
        "airgap_agi2_engine_sweep_*",
        "airgap_agi2_shards_*/shard_*",
    ):
        for d in sorted((root / "reports").glob(pattern)):
            if not d.is_dir():
                continue
            for name in ("submission.json", "submission.partial.json"):
                sources.append(d / name)
    sources.append(root / "kaggle/airgap-notebooks/arc-agi-2/payload/submission.json")

    union: Dict[str, Any] = {}
    provenance: Dict[str, str] = {}
    for path, sub in load_submissions(sources):
        for tid, preds in sub.items():
            if tid not in challenges:
                continue
            if len(preds) != len(challenges[tid]["test"]):
                continue
            new_lic = licensed_count(challenges, preds, tid)
            if tid not in union:
                union[tid] = preds
                provenance[tid] = str(path.relative_to(root))
                continue
            old_lic = licensed_count(challenges, union[tid], tid)
            if new_lic > old_lic:
                union[tid] = preds
                provenance[tid] = str(path.relative_to(root))

    # Fill missing tasks with identity so schema is complete when rebuilding
    identity_fill = 0
    for tid in ids:
        if tid not in union:
            preds = []
            for case in challenges[tid]["test"]:
                g = [list(r) for r in case["input"]]
                preds.append({"attempt_1": g, "attempt_2": [list(r) for r in g]})
            union[tid] = preds
            provenance[tid] = "identity_fill"
            identity_fill += 1

    licensed = 0
    identity = 0
    identity_task_ids = []
    for tid in ids:
        preds = union[tid]
        task_lic = licensed_count(challenges, preds, tid)
        task_id_n = len(preds) - task_lic
        licensed += task_lic
        identity += task_id_n
        if task_id_n:
            identity_task_ids.append(tid)

    canonical = (
        args.canonical_dir.resolve()
        if args.canonical_dir
        else root / "reports/airgap_agi2_test_20260721T175400Z"
    )
    canonical.mkdir(parents=True, exist_ok=True)
    sub_path = canonical / "submission.json"
    sub_path.write_text(json.dumps(union, separators=(",", ":")), encoding="utf-8")
    receipt = {
        "kind": "agi2_merged_licensed_receipt",
        "licensed_grids": licensed,
        "identity_grids": identity,
        "total_grids": licensed + identity,
        "licensed_pct": round(100.0 * licensed / max(1, licensed + identity), 2),
        "tasks": len(ids),
        "identity_fill_tasks": identity_fill,
        "identity_task_ids": identity_task_ids,
        "provenance": provenance,
        "submission_sha256": sha256(sub_path),
    }
    (canonical / "MERGED_LICENSED_VS_IDENTITY.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"MERGED licensed={licensed}/259 identity={identity} "
        f"pct={receipt['licensed_pct']} → {sub_path}",
        flush=True,
    )

    if args.rebuild_notebook:
        # Only swap platform payload when we beat current notebook licensed count
        nb_payload = root / "kaggle/airgap-notebooks/arc-agi-2/payload/submission.json"
        cur = json.loads(nb_payload.read_text(encoding="utf-8"))
        cur_lic = sum(
            licensed_count(challenges, cur[tid], tid)
            for tid in ids
            if tid in cur
        )
        if licensed > cur_lic:
            print(f"REBUILD notebook payload {cur_lic} → {licensed}", flush=True)
            cmd = [
                sys.executable,
                str(root / "scripts/build_arc_airgap_kaggle_notebooks.py"),
                "--root",
                str(root),
                "--agi2-platform-json",
                str(sub_path),
            ]
            subprocess.run(cmd, check=True)
            # refresh b64
            b64 = root / "kaggle/airgap-notebooks/arc-agi-2/embedded_submission_b64.txt"
            b64.write_text(
                base64.b64encode(nb_payload.read_bytes()).decode("ascii"),
                encoding="utf-8",
            )
        else:
            print(
                f"SKIP rebuild (merged {licensed} <= notebook {cur_lic})",
                flush=True,
            )

    print(json.dumps({k: receipt[k] for k in (
        "licensed_grids", "identity_grids", "licensed_pct", "submission_sha256"
    )}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
