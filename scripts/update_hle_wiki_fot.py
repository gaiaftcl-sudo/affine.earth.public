#!/usr/bin/env python3
"""Update wiki FoT pages with official_hle_accuracy from receipt. No tokens."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    receipt_path = Path(args.run_dir) / "official_hle_accuracy.receipt.json"
    if not receipt_path.is_file():
        raise SystemExit(f"missing {receipt_path}")
    receipt = json.loads(receipt_path.read_text())
    acc = receipt.get("official_hle_accuracy")
    n = receipt.get("n")
    judged = receipt.get("judged_count")
    miss_count = receipt.get("miss_count")
    model = receipt.get("model")
    judge = receipt.get("judge_model")
    run_rel = str(Path(args.run_dir).resolve().relative_to(root))

    score_line = (
        f"**official_hle_accuracy = {acc}%** (n={n}, judged={judged}, misses={miss_count}; "
        f"model=`{model}`; judge=`{judge}`; run `{run_rel}`). "
        f"Accuracy uses CAIS divisor n=full test set. Rotate any chat-pasted HF token after this run."
    )

    live = root / "wiki" / "Humanitys-Last-Exam-Live.md"
    if live.is_file():
        text = live.read_text()
        banner = f"\n\n## Official judged score\n\n{score_line}\n"
        if "## Official judged score" in text:
            text = re.sub(
                r"## Official judged score\n\n.*?(?=\n## |\Z)",
                banner.lstrip() + "\n",
                text,
                count=1,
                flags=re.S,
            )
        else:
            text = text.rstrip() + banner
        live.write_text(text)

    results = root / "wiki" / "Results-And-Scores.md"
    if results.is_file() and acc is not None:
        text = results.read_text()
        repl = (
            f"| Humanity's Last Exam | `hle` | **official_hle_accuracy={acc}%** "
            f"(n={n}, judged={judged}; `{run_rel}`); local drills remain local-only | "
            f"[Live](Humanitys-Last-Exam-Live) · [HLE game](Language-Games-HLE) · doctrine `f983986` |"
        )
        text2, nsub = re.subn(
            r"\| Humanity's Last Exam \| `hle` \|.*?\|",
            repl,
            text,
            count=1,
        )
        if nsub:
            results.write_text(text2)

    print(json.dumps({"updated": True, "official_hle_accuracy": acc, "run_dir": run_rel}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
