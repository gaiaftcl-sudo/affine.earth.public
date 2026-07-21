"""Unit tests for exam miss → reinject → closure loop (no Kaggle, no live LLM)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llm_llvm_bench.arc.franklin_s4_projection import (
    S4_STATUS_LOCKED,
    S4_STATUS_REINJECT,
    normalize_s4_response,
)
from llm_llvm_bench.exam.miss_reinjection import (
    ARISTOTELIAN_CLOSURE_TURNS,
    TRACK_ARC2,
    TRACK_HLE,
    LoopState,
    MissRecord,
    acquire_writer_lock,
    apply_local_s4_validator,
    discover_owned_hybrid_green,
    extract_json_object,
    load_fail_receipts,
    normalize_repair_payload,
    run_reinjection_cycle,
    sync_local_solver_green,
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
        '"s3":"xform","s4":{"typed_candidate":"shape_lock","validator":"demonstration_replay",'
        '"status":"REINJECT","unresolved_alternatives":[]},'
        '"grammar_update":"fix","repair_kind":"grammar",'
        '"research_note":"n","closure_ready":false}\n```\n'
        "done"
    )
    parsed = extract_json_object(prose)
    assert parsed is not None
    assert parsed["s4"]["status"] == "REINJECT"
    assert parsed["s1"] == "obj"


def test_extract_json_object_prefers_repair_shaped_nested() -> None:
    text = (
        '{"meta":{"ok":true},"noise":1,'
        '"repair":{"task_id":"t1","track":"arc2","s1":"a","s2":"b","s3":"c",'
        '"s4":{"typed_candidate":"LOCK","validator":"demonstration_replay",'
        '"status":"LOCKED","unresolved_alternatives":[]},'
        '"grammar_update":"g","repair_kind":"grammar","research_note":"r",'
        '"closure_ready":true}}'
    )
    raw = extract_json_object(text)
    miss = MissRecord(track="arc2", task_id="t1", evidence={}, source_path="x")
    normalized = normalize_repair_payload(raw, miss)
    assert normalized is not None
    assert normalized["s4_status"] == S4_STATUS_LOCKED
    assert normalized["c4_invariant"] == "LOCK"
    assert normalized["closure_ready"] is True


def test_normalize_accepts_protocol_and_rejects_dry_run() -> None:
    miss = MissRecord(track="arc2", task_id="x", evidence={}, source_path="x")
    ok = normalize_repair_payload(
        {
            "S1": "o",
            "S2": "r",
            "S3": "t",
            "typed_candidate": "live_lock",
            "validator": "demonstration_replay",
            "status": "LOCKED",
            "unresolved_alternatives": [],
            "grammar": "g",
        },
        miss,
    )
    assert ok is not None
    assert ok["s4_status"] == S4_STATUS_LOCKED
    assert ok["c4_invariant"] == "live_lock"
    assert ok["validator"] == "demonstration_replay"
    assert ok["grammar_update"] == "g"
    assert (
        normalize_repair_payload(
            {"s1": "DRY_RUN", "typed_candidate": "DRY_RUN", "status": "REINJECT"},
            miss,
        )
        is None
    )


def test_normalize_legacy_c4_alias_maps_to_reinject() -> None:
    miss = MissRecord(track="arc2", task_id="x", evidence={}, source_path="x")
    ok = normalize_s4_response(
        {"S1": "o", "S2": "r", "S3": "t", "S4": "b", "C4": "live_lock", "grammar": "g"},
        track="arc2",
        task_id="x",
    )
    assert ok is not None
    assert ok["s4_status"] == S4_STATUS_REINJECT
    assert ok["c4_invariant"] == "live_lock"


def test_apply_local_validator_demotes_empty_locked() -> None:
    miss = MissRecord(track="arc2", task_id="t", evidence={}, source_path="x")
    repair = {
        "s4_status": S4_STATUS_LOCKED,
        "typed_candidate": "",
        "validator": "demonstration_replay",
        "unresolved_alternatives": ["a"],
        "c4_invariant": "",
    }
    out = apply_local_s4_validator(miss, repair)
    assert out["s4_status"] == S4_STATUS_REINJECT
    assert out["validator_result"]["ran"] is True
    assert out["validator_result"]["accepted"] is False


def test_apply_local_validator_locks_hle_exact_match() -> None:
    miss = MissRecord(
        track="hle",
        task_id="q",
        evidence={"expected": "B"},
        source_path="x",
    )
    repair = {
        "s4_status": S4_STATUS_LOCKED,
        "typed_candidate": "B",
        "validator": "exact_format_check",
        "unresolved_alternatives": [],
        "c4_invariant": "B",
    }
    out = apply_local_s4_validator(miss, repair)
    assert out["s4_status"] == S4_STATUS_LOCKED
    assert out["validator_result"]["accepted"] is True
    assert out["closure_ready"] is True


def test_salvage_truncated_s4_json() -> None:
    from llm_llvm_bench.exam.miss_reinjection import salvage_s4_from_text

    miss = MissRecord(track="arc2", task_id="135a2760", evidence={}, source_path="x")
    truncated = (
        '{"task_id":"135a2760","track":"arc2","s1":"a","s2":"b","s3":"c",'
        '"s4":{"typed_candidate":"horiz_reflect","validator":"demonstration_replay",'
        '"status":"REINJECT","unresolved_alternatives":["Horiz'
    )
    salvaged = salvage_s4_from_text(truncated, miss)
    assert salvaged is not None
    assert salvaged["s4_status"] == S4_STATUS_REINJECT
    assert salvaged["typed_candidate"] == "horiz_reflect"
    assert salvaged["validator"] == "demonstration_replay"


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


def test_sync_local_solver_green_closes_owned_exact() -> None:
    owned = discover_owned_hybrid_green(ROOT)
    assert "136b0064" in owned
    assert owned["136b0064"]["engine"] == "s1_digit_separator_snake"
    assert "135a2760" in owned
    state = LoopState(
        tasks={
            "arc2:136b0064": {
                "track": "arc2",
                "task_id": "136b0064",
                "status": "HEALING",
                "last_c4": "REINJECT:slice",
                "last_gate": "S4_REINJECT",
                "turn_count": 3,
            }
        }
    )
    skipped = sync_local_solver_green(state, ROOT)
    assert "arc2:136b0064" in skipped
    task = state.tasks["arc2:136b0064"]
    assert task["status"] == "CLOSED"
    assert task["engine"] == "s1_digit_separator_snake"
    assert not str(task["last_c4"]).startswith("REINJECT")
    assert task["last_gate"] in {"LOCAL_SOLVER_GREEN", "S4_LOCKED"}


def test_load_arc2_skips_owned_green_and_dedupes() -> None:
    misses = load_fail_receipts(ROOT, tracks=(TRACK_ARC2,), per_track_limit=6)
    ids = [m.task_id for m in misses]
    assert "136b0064" not in ids
    assert "135a2760" not in ids
    assert len(ids) == len(set(ids))
