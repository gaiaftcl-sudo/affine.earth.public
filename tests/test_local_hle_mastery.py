"""Regression checks for local HLE language-game drill contracts."""

from __future__ import annotations

from scripts.run_local_hle_mastery import FIXTURES, apply_reinjection_turns, DATASET_REVISION


def test_local_fixture_set_covers_core_answer_contracts() -> None:
    move_types = {fixture["move_type"] for fixture in FIXTURES}
    assert {
        "mcq",
        "exact_match",
        "multimodal_stub",
        "boolean",
        "numeric_exact",
        "mathematical_expression",
        "unit_bearing_exact",
        "short_exact_answer",
        "ordered_exact_sequence",
        "percentage_exact",
        "base_conversion",
        "roman_numeral",
        "multi_hop_exact",
        "code_token_exact",
        "inequality_boolean",
        "set_cardinality",
        "temporal_exact",
        "matrix_shape_exact",
        "logic_mcq",
        "s4_multi_turn_exact",
        "scientific_notation_exact",
        "permutation_exact",
        "acronym_exact",
    } <= move_types
    assert len(FIXTURES) >= 24
    assert DATASET_REVISION.startswith("local-synthetic-hle-fixtures-v")


def test_local_fixture_ids_unique() -> None:
    ids = [fixture["id"] for fixture in FIXTURES]
    assert len(ids) == len(set(ids))


def test_local_miss_reinjection_replaces_only_verified_answer() -> None:
    fixture = {"id": "q-1", "expected": "B", "answer_format": "option_letter"}
    result = {
        "matched": False,
        "answer": "A",
        "context": "initial",
        "identity_bound": True,
        "format_ok": True,
        "turns": [],
    }
    reinjected = {
        "attempted": True,
        "answer": "B",
        "context": "re-read contract",
        "returned_question_id": "q-1",
        "returned_answer_format": "option_letter",
        "identity_bound": True,
        "format_ok": True,
        "matched": True,
    }

    apply_reinjection_turns(result, reinjected, fixture)

    assert result["initial_matched"] is False
    assert result["matched"] is True
    assert result["answer"] == "B"
    assert [turn["turn_kind"] for turn in result["turns"]] == [
        "REINJECT",
        "CONTEXT",
        "ANSWER",
        "GATE",
    ]
    assert result["turns"][-1]["gate_verdict"] == "LOCAL_REINJECTION_MATCH"
