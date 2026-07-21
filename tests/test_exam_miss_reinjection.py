"""Unit tests for exam miss → reinject → closure loop (no Kaggle, no live LLM)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llm_llvm_bench.exam.miss_reinjection import (
    ARISTOTELIAN_CLOSURE_TURNS,
    TRACK_ARC2,
    TRACK_HLE,
    MissRecord,
    acquire_writer_lock,
    extract_json_object,
    load_fail_receipts,
    normalize_repair_payload,
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


def test_extract_json_object_from_reasoning_prose() -> None:
    prose = (
        "Thinking...\n"
        "Here is the payload:\n"
        '```json\n{"task_id":"135a2760","track":"arc2","s1":"obj","s2":"rel",'
        '"s3":"xform","s4":"accept","c4_invariant":"shape_lock",'
        '"grammar_update":"fix","repair_kind":"grammar",'
        '"research_note":"n","closure_ready":false}\n```\n'
        "done"
    )
    parsed = extract_json_object(prose)
    assert parsed is not None
    assert parsed["c4_invariant"] == "shape_lock"
    assert parsed["s1"] == "obj"


def test_extract_json_object_prefers_repair_shaped_nested() -> None:
    text = (
        '{"meta":{"ok":true},"noise":1,'
        '"repair":{"task_id":"t1","track":"arc2","s1":"a","s2":"b","s3":"c",'
        '"s4":"d","c4_invariant":"LOCK","grammar_update":"g",'
        '"repair_kind":"grammar","research_note":"r","closure_ready":true}}'
    )
    raw = extract_json_object(text)
    miss = MissRecord(track="arc2", task_id="t1", evidence={}, source_path="x")
    normalized = normalize_repair_payload(raw, miss)
    assert normalized is not None
    assert normalized["c4_invariant"] == "LOCK"
    assert normalized["closure_ready"] is True


def test_normalize_accepts_c4_alias_and_rejects_dry_run() -> None:
    miss = MissRecord(track="arc2", task_id="x", evidence={}, source_path="x")
    ok = normalize_repair_payload(
        {"S1": "o", "S2": "r", "S3": "t", "S4": "b", "C4": "live_lock", "grammar": "g"},
        miss,
    )
    assert ok is not None
    assert ok["c4_invariant"] == "live_lock"
    assert ok["grammar_update"] == "g"
    assert (
        normalize_repair_payload(
            {"s1": "DRY_RUN", "c4_invariant": "DRY_RUN", "grammar_update": "x"}, miss
        )
        is None
    )


def test_dry_run_refused_when_live_lock_held(tmp_path: Path) -> None:
    state_dir = tmp_path / "exam_reinjection"
    acquire_writer_lock(state_dir, dry_run=False)
    with pytest.raises(RuntimeError, match="Refuse --dry-run"):
        run_reinjection_cycle(
            ROOT,
            state_dir=state_dir,
            tracks=(TRACK_ARC2,),
            per_track_limit=1,
            mastery_mode="none",
            dry_run=True,
        )
