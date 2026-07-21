#!/usr/bin/env python3
"""CLI driver for the permanent exam miss → reinject → closure loop.

See docs/EXAM_MISS_REINJECTION_LOOP.md.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from llm_llvm_bench.exam.miss_reinjection import (  # noqa: E402
    TRACK_ARC2,
    TRACK_ARC3,
    TRACK_HLE,
    run_reinjection_cycle,
)


def parse_tracks(raw: str) -> tuple[str, ...]:
    mapping = {
        "arc2": TRACK_ARC2,
        "arc-2": TRACK_ARC2,
        "agi2": TRACK_ARC2,
        "arc3": TRACK_ARC3,
        "arc-3": TRACK_ARC3,
        "agi3": TRACK_ARC3,
        "hle": TRACK_HLE,
        "all": "ALL",
    }
    parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
    if not parts or "all" in parts:
        return (TRACK_ARC2, TRACK_ARC3, TRACK_HLE)
    out = []
    for part in parts:
        if part not in mapping or mapping[part] == "ALL":
            raise SystemExit(f"Unknown track: {part}")
        out.append(mapping[part])
    return tuple(dict.fromkeys(out))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=_REPO_ROOT)
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="Persistent loop state (default: reports/exam_reinjection)",
    )
    parser.add_argument("--tracks", default="all", help="arc2,arc3,hle or all")
    parser.add_argument("--per-track-limit", type=int, default=4)
    parser.add_argument(
        "--mastery",
        choices=("none", "affected", "full"),
        default="affected",
        help="Re-run local mastery after Franklin repair (never Kaggle)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(__import__("os").environ.get("EXAM_REINJECT_TIMEOUT", "300")),
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=int(__import__("os").environ.get("EXAM_REINJECT_MAX_TOKENS", "1024")),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip Franklin HTTP; still load misses and record grammar placeholders",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single cycle and exit (default unless --daemon)",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Re-run continuously; never idle between cycles",
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=30,
        help="Sleep between daemon cycles (default 30)",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=0,
        help="Daemon stop after N cycles (0 = forever)",
    )
    args = parser.parse_args()

    if args.daemon and args.once:
        raise SystemExit("Choose either --daemon or --once, not both")
    if args.dry_run and __import__("os").environ.get("EXAM_REINJECT_LIVE") == "1":
        raise SystemExit("EXAM_REINJECT_LIVE=1 forbids --dry-run")
    once = args.once or not args.daemon
    tracks = parse_tracks(args.tracks)
    root = args.root.resolve()
    cycles = 0

    # Daemon holds exclusive writer lock across cycles so dry-run cannot clobber.
    if args.daemon and not args.dry_run:
        __import__("os").environ["EXAM_REINJECT_HOLD_LOCK"] = "1"
        __import__("os").environ.setdefault("EXAM_REINJECT_LIVE", "1")

    while True:
        summary = run_reinjection_cycle(
            root,
            state_dir=args.state_dir.resolve() if args.state_dir else None,
            tracks=tracks,
            per_track_limit=args.per_track_limit,
            mastery_mode=args.mastery,
            timeout=args.timeout,
            max_tokens=args.max_tokens,
            dry_run=args.dry_run,
        )
        cycles += 1
        if summary.get("dry_run") and not args.dry_run:
            raise SystemExit("BUG: live argv stamped dry_run=True — abort")
        print(json.dumps(summary, indent=2, sort_keys=True))
        print(
            f"Cycle {summary['cycle']}: actioned={summary['misses_actioned']} "
            f"open={summary['open_tasks']} closed={summary['closed_tasks']} "
            f"dead_end={summary['dead_end_tasks']} "
            f"franklin_turns={summary['total_franklin_turns']} "
            f"dry_run={summary.get('dry_run')} "
            f"(Aristotelian budget {summary['aristotelian_closure_turns']})"
        )
        if once:
            # Non-zero if Franklin failed on any row (daemon keeps going).
            failed = any(not row.get("franklin_ok", True) for row in summary.get("rows") or [])
            return 1 if failed and not args.dry_run else 0
        if args.max_cycles and cycles >= args.max_cycles:
            return 0
        time.sleep(max(1, args.interval_seconds))


if __name__ == "__main__":
    sys.exit(main())
