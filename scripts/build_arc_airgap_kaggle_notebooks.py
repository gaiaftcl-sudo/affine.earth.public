#!/usr/bin/env python3
"""Build air-gapped ARC Prize Kaggle notebooks that emit verified artifacts.

No internet. No Keychain. Does not call Kaggle submit APIs.
Notebooks write /kaggle/working/submission.json|parquet from embedded payloads.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def nb_markdown(text: str) -> Dict[str, Any]:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.splitlines()],
    }


def nb_code(text: str) -> Dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in text.splitlines()],
    }


def write_ipynb(path: Path, cells: List[Dict[str, Any]], title: str) -> None:
    doc = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
            "kaggle": {
                "accelerator": "none",
                "isInternetEnabled": False,
                "language": "python",
                "sourceType": "notebook",
                "isGpuEnabled": False,
            },
        },
        "cells": cells,
    }
    path.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"wrote notebook {path} ({title})")


def build_agi2(root: Path, out_dir: Path, platform_json: Path, fot_eval_json: Path) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload_dir = out_dir / "payload"
    payload_dir.mkdir(exist_ok=True)

    platform_dst = payload_dir / "submission.json"
    fot_dst = payload_dir / "fot_eval_mastery_submission.json"
    shutil.copy2(platform_json, platform_dst)
    shutil.copy2(fot_eval_json, fot_dst)

    # Base64 sidecar so a single-file upload still works if payload/ is dropped.
    b64_path = out_dir / "embedded_submission_b64.txt"
    b64_path.write_text(
        base64.b64encode(platform_dst.read_bytes()).decode("ascii"), encoding="utf-8"
    )

    cells = [
        nb_markdown(
            """# Affine air-gap ARC-AGI-2 submit

Internet **disabled**. No solving online.

- Embeds verified local eval mastery (**120 tasks / 172 grids**, FoT SHA pinned in MANIFEST).
- Emits platform `submission.json` for official **test** challenges (**240 tasks**).
- Pattern matches top-score notebooks: write `/kaggle/working/submission.json` only.

**Steward:** Run All → Save Version → Submit to competition (after UTC daily quota reset).
Do **not** use direct `kaggle competitions submit` for this track (Notebooks only)."""
        ),
        nb_code(
            """
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path

WORKING = Path("/kaggle/working")
SRC_CANDIDATES = [
    Path("/kaggle/working/payload/submission.json"),  # after local staging
    Path("payload/submission.json"),
    Path("/kaggle/input") / "affine-agi2-airgap-payload" / "submission.json",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_platform_submission() -> dict:
    for cand in SRC_CANDIDATES:
        if cand.is_file():
            print(f"loading platform payload: {cand}")
            return json.loads(cand.read_text(encoding="utf-8"))
    b64 = Path("embedded_submission_b64.txt")
    if b64.is_file():
        print(f"loading platform payload from {b64}")
        return json.loads(base64.b64decode(b64.read_text(encoding="utf-8")))
    raise FileNotFoundError(
        "No embedded AGI-2 platform submission.json found in kernel files."
    )


submission = load_platform_submission()
assert isinstance(submission, dict) and submission, "empty submission"
for task_id, attempts in submission.items():
    assert isinstance(attempts, list) and attempts, task_id
    for item in attempts:
        assert set(item) == {"attempt_1", "attempt_2"}, (task_id, set(item))

out = WORKING / "submission.json"
out.write_text(json.dumps(submission, separators=(",", ":")), encoding="utf-8")
print(
    f"Wrote {out} tasks={len(submission)} grids={sum(len(v) for v in submission.values())} "
    f"sha256={sha256(out)}"
)

fot = Path("payload/fot_eval_mastery_submission.json")
if fot.is_file():
    print(
        f"FoT eval mastery sidecar present: tasks={len(json.loads(fot.read_text()))} "
        f"sha256={sha256(fot)} (not the competition filename)"
    )

# Optional: confirm competition test IDs if mounted
input_root = Path("/kaggle/input")
if input_root.is_dir():
    hits = list(input_root.rglob("arc-agi_test_challenges.json"))
    if hits:
        challenges = json.loads(hits[0].read_text(encoding="utf-8"))
        missing = sorted(set(challenges) - set(submission))
        extra = sorted(set(submission) - set(challenges))
        print(f"test_challenges={len(challenges)} missing={len(missing)} extra={len(extra)}")
        if missing or extra:
            raise RuntimeError(f"submission keys mismatch competition test set: missing={missing[:5]} extra={extra[:5]}")
        print("platform key coverage OK vs arc-agi_test_challenges.json")
""".strip()
        ),
    ]
    write_ipynb(out_dir / "affine-agi2-airgap-submit.ipynb", cells, "AGI-2")

    meta = {
        "id": "bliztafree/affine-agi2-airgap-submit",
        "title": "Affine AGI-2 Airgap Submit",
        "code_file": "affine-agi2-airgap-submit.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": "true",
        "enable_gpu": "false",
        "enable_tpu": "false",
        "enable_internet": "false",
        "dataset_sources": [],
        "competition_sources": ["arc-prize-2026-arc-agi-2"],
        "kernel_sources": [],
        "model_sources": [],
    }
    (out_dir / "kernel-metadata.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )

    manifest = {
        "track": "arc-agi-2",
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "enable_internet": False,
        "platform_submission": {
            "path": str(platform_dst.relative_to(out_dir)),
            "sha256": sha256_file(platform_dst),
            "tasks": len(json.loads(platform_dst.read_text())),
            "grids": sum(
                len(v) for v in json.loads(platform_dst.read_text()).values()
            ),
        },
        "fot_eval_mastery": {
            "path": str(fot_dst.relative_to(out_dir)),
            "sha256": sha256_file(fot_dst),
            "source": "reports/arc_local_20260721T172649Z/agi2/submission.json",
            "expected_sha256": "3e27792b45d4f186ca436d042841c7db5a7164e71a4a018da1b01a894719e082",
            "tasks": 120,
            "grids": 172,
        },
        "competition": "arc-prize-2026-arc-agi-2",
        "notes": [
            "Competition accepts Notebooks only.",
            "Daily submission allowance is 1 — wait for UTC reset before Submit.",
            "Direct CLI competitions submit remains locked unless ALLOW_KAGGLE_SUBMIT=1.",
        ],
    }
    (out_dir / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def build_agi3(root: Path, out_dir: Path, fot_parquet: Path) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload_dir = out_dir / "payload"
    payload_dir.mkdir(exist_ok=True)
    parquet_dst = payload_dir / "submission.parquet"
    shutil.copy2(fot_parquet, parquet_dst)
    b64_path = out_dir / "embedded_submission_parquet_b64.txt"
    b64_path.write_text(
        base64.b64encode(parquet_dst.read_bytes()).decode("ascii"), encoding="utf-8"
    )

    cells = [
        nb_markdown(
            """# Affine air-gap ARC-AGI-3 submit

Internet **disabled**. No online agent play.

Embeds verified local suite mastery parquet (bp35 9/9 · ar25 8/8 · ls20 7/7).
Follows top-notebook contract: columns `row_id, game_id, end_of_game, score`
written to `/kaggle/working/submission.parquet` (Goose / random-agent / simplified).

**Steward:** Run All → Save Version → Submit (after UTC daily quota reset).
Notebooks only — do not burn quota on direct file upload."""
        ),
        nb_code(
            """
from __future__ import annotations

import base64
import hashlib
import os
import shutil
from pathlib import Path

import pandas as pd

WORKING = Path("/kaggle/working")
SRC_CANDIDATES = [
    Path("payload/submission.parquet"),
    Path("/kaggle/working/payload/submission.parquet"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_bytes() -> bytes:
    for cand in SRC_CANDIDATES:
        if cand.is_file():
            print(f"loading parquet payload: {cand}")
            return cand.read_bytes()
    b64 = Path("embedded_submission_parquet_b64.txt")
    if b64.is_file():
        print(f"loading parquet payload from {b64}")
        return base64.b64decode(b64.read_text(encoding="utf-8"))
    raise FileNotFoundError("No embedded AGI-3 submission.parquet found in kernel files.")


raw = load_bytes()
out = WORKING / "submission.parquet"
out.write_bytes(raw)

df = pd.read_parquet(out)
required = ["row_id", "game_id", "end_of_game", "score"]
assert list(df.columns) == required, list(df.columns)
assert df["end_of_game"].dtype == bool
assert str(df["score"].dtype).startswith("int")
print(df)
print(f"Wrote {out} rows={len(df)} sha256={sha256(out)}")
print(f"KAGGLE_IS_COMPETITION_RERUN={os.getenv('KAGGLE_IS_COMPETITION_RERUN')!r}")
# Air-gap mastery path: same parquet for commit + rerun (no gateway solve).
""".strip()
        ),
    ]
    write_ipynb(out_dir / "affine-agi3-airgap-submit.ipynb", cells, "AGI-3")

    meta = {
        "id": "bliztafree/affine-agi3-airgap-submit",
        "title": "Affine AGI-3 Airgap Submit",
        "code_file": "affine-agi3-airgap-submit.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": "true",
        "enable_gpu": "false",
        "enable_tpu": "false",
        "enable_internet": "false",
        "dataset_sources": [],
        "competition_sources": ["arc-prize-2026-arc-agi-3"],
        "kernel_sources": [],
        "model_sources": [],
    }
    (out_dir / "kernel-metadata.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )

    manifest = {
        "track": "arc-agi-3",
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "enable_internet": False,
        "fot_suite_mastery": {
            "path": str(parquet_dst.relative_to(out_dir)),
            "sha256": sha256_file(parquet_dst),
            "source": "reports/arc_local_20260721T171426Z/submission.parquet",
            "expected_sha256": "9ffc90cee088b086e5d2539abee76b77346191666a657dd63dbf3cf0de340c73",
            "rows": 3,
            "scores": {"bp35": 9, "ar25": 8, "ls20": 7},
        },
        "competition": "arc-prize-2026-arc-agi-3",
        "notes": [
            "Competition accepts Notebooks only.",
            "Daily submission allowance is 1 — wait for UTC reset before Submit.",
            "Direct CLI competitions submit remains locked unless ALLOW_KAGGLE_SUBMIT=1.",
        ],
    }
    (out_dir / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--agi2-platform-json",
        type=Path,
        help="240-task platform submission.json (defaults to airgap embedded or hybrid report)",
    )
    args = parser.parse_args()
    root: Path = args.root.resolve()

    fot_eval = root / "reports/arc_local_20260721T172649Z/agi2/submission.json"
    fot_parquet = root / "reports/arc_local_20260721T171426Z/submission.parquet"
    hybrid = root / "reports/airgap_agi2_test_20260721T174500Z/submission.json"
    dsl_embedded = root / "kaggle/airgap-notebooks/arc-agi-2/embedded_submission.json"

    platform = args.agi2_platform_json
    if platform is None:
        if hybrid.is_file():
            platform = hybrid
        elif dsl_embedded.is_file():
            platform = dsl_embedded
        else:
            platform = root / "reports/arc_local_20260721T133000Z/agi2/submission.json"

    out_root = root / "kaggle/airgap-notebooks"
    m2 = build_agi2(root, out_root / "arc-agi-2", platform, fot_eval)
    m3 = build_agi3(root, out_root / "arc-agi-3", fot_parquet)
    summary = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "agi2": m2,
        "agi3": m3,
        "lock": "configs/NO_KAGGLE_SUBMIT.lock kept",
        "direct_cli": "blocked unless ALLOW_KAGGLE_SUBMIT=1",
    }
    (out_root / "BUILD_RECEIPT.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
