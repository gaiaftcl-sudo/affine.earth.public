"""Unit tests for exam miss → reinject → closure loop (no Kaggle, no live LLM)."""

from __future__ import annotations

import json
from pathlib import Path

from llm_llvm_bench.exam.miss_reinjection import (
    ARISTOTELIAN_CLOSURE_TURNS,
    TRACK_ARC2,
    TRACK_HLE,
    load_fail_receipts,
    run_reinjection_cycle,
)

ROOT = Path(__file__).resolve().parents[1]


def test_aristotelian_budget_is_29() -> None:
    assert ARISTOTELIAN_CLOSURE_TURNS == 29


def test_load_fail_receipts_from_local_reports() -> None:
    misses = load_fail_receipts(ROOT, per_track_limit=3)
    tracks = {m.track for m in misses}
    # At least one track should surface from checked-in / generated reports.
    assert tracks
    for miss in misses:
        assert miss.task_id
        assert miss.source_path
        assert miss.s_state


def test_dry_run_cycle_writes_state(tmp_path: Path) -> None:
    lock = ROOT / "configs" / "NO_KAGGLE_SUBMIT.lock"
    assert lock.is_file()
    state_dir = tmp_path / "exam_reinjection"
    summary = run_reinjection_cycle(
        ROOT,
        state_dir=state_dir,
        tracks=(TRACK_ARC2, TRACK_HLE),
        per_track_limit=2,
        mastery_mode="none",
        dry_run=True,
    )
    assert summary["kaggle_submit"] is False
    assert summary["no_kaggle_submit_lock"] is True
    assert summary["dry_run"] is True
    assert (state_dir / "state.json").is_file()
    assert (state_dir / "latest_cycle.json").is_file()
    assert (state_dir / "turns.jsonl").is_file()
    state = json.loads((state_dir / "state.json").read_text(encoding="utf-8"))
    assert state["aristotelian_closure_turns"] == 29
    assert state["cycles"] == 1
