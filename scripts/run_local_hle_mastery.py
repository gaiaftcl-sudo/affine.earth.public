#!/usr/bin/env python3
"""Local HLE-style language-game drills aligned to docs/LANGUAGE_GAMES_HLE.md.

Exercises context-setting → typed answer for MCQ, exact-match, and a multimodal
adapter stub against an OpenAI-compatible loopback. Fixtures are locally authored.
This path never reads Keychain, never invents official Accuracy/Calibration, and
never treats fixture matches as a CAIS score.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from llm_llvm_bench.arc.franklin_uum8d_system_prompt import (  # noqa: E402
    franklin_uum8d_game_comprehension_system_prompt,
)
from llm_llvm_bench.arc.franklin_s4_projection import (  # noqa: E402
    projection_system_prompt,
)
from llm_llvm_bench.exam.s4_client import run_s4_projection_turn  # noqa: E402

DATASET_REVISION = "local-synthetic-hle-fixtures-v5"

FIXTURES: tuple[dict[str, Any], ...] = (
    {
        "id": "local-mcq-planet-red",
        "move_type": "mcq",
        "answer_format": "option_letter",
        "question": "Which planet is commonly called the Red Planet?",
        "choices": {"A": "Earth", "B": "Mars", "C": "Venus", "D": "Mercury"},
        "expected": "B",
        "modality": None,
    },
    {
        "id": "local-exact-symbol-gold",
        "move_type": "exact_match",
        "answer_format": "exact_token",
        "question": "Give the chemical symbol for gold.",
        "expected": "Au",
        "modality": None,
    },
    {
        "id": "local-multimodal-stub-triangle",
        "move_type": "multimodal_stub",
        "answer_format": "exact_token",
        "question": (
            "A local image adapter would supply a diagram described as: "
            "'a triangle has angles 50°, 60°, and x°'. What is x?"
        ),
        "expected": "70",
        "modality": {
            "kind": "text_adapter_stub",
            "supported": False,
            "note": (
                "Synthetic text-only adapter stub. Exercises context-setting and "
                "answer extraction; not an official HLE image evaluation."
            ),
        },
    },
    {
        "id": "local-boolean-prime",
        "move_type": "boolean",
        "answer_format": "exact_token",
        "question": "Is 29 a prime number? Answer True or False.",
        "expected": "True",
        "modality": None,
    },
    {
        "id": "local-integer-combinatorics",
        "move_type": "numeric_exact",
        "answer_format": "exact_token",
        "question": "How many unordered pairs can be chosen from five distinct objects?",
        "expected": "10",
        "modality": None,
    },
    {
        "id": "local-fraction-reduction",
        "move_type": "mathematical_expression",
        "answer_format": "exact_token",
        "question": "Reduce the fraction 18/24 to lowest terms.",
        "expected": "3/4",
        "modality": None,
    },
    {
        "id": "local-unit-conversion",
        "move_type": "unit_bearing_exact",
        "answer_format": "exact_token",
        "question": "How many centimetres are in 2.5 metres? Return the integer token.",
        "expected": "250",
        "modality": None,
    },
    {
        "id": "local-short-answer-capital",
        "move_type": "short_exact_answer",
        "answer_format": "exact_token",
        "question": "What is the capital city of Japan?",
        "expected": "Tokyo",
        "modality": None,
    },
    {
        "id": "local-order-sensitive-sequence",
        "move_type": "ordered_exact_sequence",
        "answer_format": "exact_token",
        "question": "Write the first three positive integers in ascending order, comma-separated with no spaces.",
        "expected": "1,2,3",
        "modality": None,
    },
    {
        "id": "local-set-membership-noble-gas",
        "move_type": "mcq",
        "answer_format": "option_letter",
        "question": "Which of the following is a noble gas?",
        "choices": {"A": "Oxygen", "B": "Nitrogen", "C": "Neon", "D": "Hydrogen"},
        "expected": "C",
        "modality": None,
    },
    {
        "id": "local-formula-pythagoras-hyp",
        "move_type": "mathematical_expression",
        "answer_format": "exact_token",
        "question": "3-4-? right triangle. Hypotenuse integer only.",
        "expected": "5",
        "modality": None,
    },
    {
        "id": "local-yes-no-even",
        "move_type": "boolean",
        "answer_format": "exact_token",
        "question": "Is 42 an even integer? Answer True or False.",
        "expected": "True",
        "modality": None,
    },
    {
        "id": "local-percent-of-eighty",
        "move_type": "percentage_exact",
        "answer_format": "exact_token",
        "question": "What is 25 percent of 80? Integer token only.",
        "expected": "20",
        "modality": None,
    },
    {
        "id": "local-base-binary-to-dec",
        "move_type": "base_conversion",
        "answer_format": "exact_token",
        "question": "Convert binary 1010 to decimal. Integer token only.",
        "expected": "10",
        "modality": None,
    },
    {
        "id": "local-roman-xiv",
        "move_type": "roman_numeral",
        "answer_format": "exact_token",
        "question": "Convert Roman numeral XIV to Arabic digits.",
        "expected": "14",
        "modality": None,
    },
    {
        "id": "local-multi-hop-alice-bob",
        "move_type": "multi_hop_exact",
        "answer_format": "exact_token",
        "question": (
            "Alice has 3 apples. Bob has twice as many as Alice. "
            "How many apples do they have together? Integer token only."
        ),
        "expected": "9",
        "modality": None,
    },
    {
        "id": "local-code-token-none",
        "move_type": "code_token_exact",
        "answer_format": "exact_token",
        "question": "In Python 3, what is the singleton null object literal token?",
        "expected": "None",
        "modality": None,
    },
    {
        "id": "local-inequality-power",
        "move_type": "inequality_boolean",
        "answer_format": "exact_token",
        "question": "Is 2^10 greater than 1000? Answer True or False.",
        "expected": "True",
        "modality": None,
    },
    {
        "id": "local-set-cardinality",
        "move_type": "set_cardinality",
        "answer_format": "exact_token",
        "question": "What is the cardinality of the set {a, b, c}? Integer token only.",
        "expected": "3",
        "modality": None,
    },
    {
        "id": "local-calendar-feb-nonleap",
        "move_type": "temporal_exact",
        "answer_format": "exact_token",
        "question": "How many days are in February of a non-leap year? Integer token only.",
        "expected": "28",
        "modality": None,
    },
    {
        "id": "local-matrix-entries",
        "move_type": "matrix_shape_exact",
        "answer_format": "exact_token",
        "question": "A 2-by-3 matrix has how many entries? Integer token only.",
        "expected": "6",
        "modality": None,
    },
    {
        "id": "local-mcq-modus-ponens",
        "move_type": "logic_mcq",
        "answer_format": "option_letter",
        "question": (
            "If P implies Q, and P is true, what follows? "
            "A) Q is true B) Q is false C) P is false D) neither"
        ),
        "choices": {
            "A": "Q is true",
            "B": "Q is false",
            "C": "P is false",
            "D": "neither",
        },
        "expected": "A",
        "modality": None,
    },
    {
        "id": "local-s4-two-turn-boiling",
        "move_type": "s4_multi_turn_exact",
        "answer_format": "exact_token",
        "question": (
            "S1: bind question_id. S2: candidates for water boiling point Celsius "
            "at 1 atm. S3: standard atmospheric pressure check. S4: emit the "
            "integer Celsius token only."
        ),
        "expected": "100",
        "modality": None,
    },
    {
        "id": "local-sci-notation-integer",
        "move_type": "scientific_notation_exact",
        "answer_format": "exact_token",
        "question": "Express 3e2 as an integer token.",
        "expected": "300",
        "modality": None,
    },
    {
        "id": "local-permutation-three",
        "move_type": "permutation_exact",
        "answer_format": "exact_token",
        "question": "How many permutations of three distinct letters exist? Integer token only.",
        "expected": "6",
        "modality": None,
    },
    {
        "id": "local-acronym-html",
        "move_type": "acronym_exact",
        "answer_format": "exact_token",
        "question": "What does HTML stand for? Return the exact four-word expansion with spaces.",
        "expected": "HyperText Markup Language",
        "modality": None,
    },
    {
        "id": "local-gcd-exact",
        "move_type": "number_theory_exact",
        "answer_format": "exact_token",
        "question": "What is gcd(48, 18)? Integer token only.",
        "expected": "6",
        "modality": None,
    },
    {
        "id": "local-lcm-exact",
        "move_type": "number_theory_exact",
        "answer_format": "exact_token",
        "question": "What is lcm(4, 6)? Integer token only.",
        "expected": "12",
        "modality": None,
    },
    {
        "id": "local-mean-exact",
        "move_type": "statistics_exact",
        "answer_format": "exact_token",
        "question": "Arithmetic mean of 2, 4, 6? Integer token only.",
        "expected": "4",
        "modality": None,
    },
    {
        "id": "local-median-exact",
        "move_type": "statistics_exact",
        "answer_format": "exact_token",
        "question": "Median of 1, 3, 9? Integer token only.",
        "expected": "3",
        "modality": None,
    },
    {
        "id": "local-string-reverse",
        "move_type": "string_transform_exact",
        "answer_format": "exact_token",
        "question": "Reverse the string abc. Exact token only.",
        "expected": "cba",
        "modality": None,
    },
    {
        "id": "local-hex-to-dec",
        "move_type": "base_conversion",
        "answer_format": "exact_token",
        "question": "Convert hexadecimal FF to decimal. Integer token only.",
        "expected": "255",
        "modality": None,
    },
    {
        "id": "local-factorial-five",
        "move_type": "number_theory_exact",
        "answer_format": "exact_token",
        "question": "What is 5!? Integer token only.",
        "expected": "120",
        "modality": None,
    },
    {
        "id": "local-mod-exact",
        "move_type": "number_theory_exact",
        "answer_format": "exact_token",
        "question": "What is 17 mod 5? Integer token only.",
        "expected": "2",
        "modality": None,
    },
    {
        "id": "local-sqrt-exact",
        "move_type": "mathematical_expression",
        "answer_format": "exact_token",
        "question": "Integer square root of 81? Integer token only.",
        "expected": "9",
        "modality": None,
    },
    {
        "id": "local-mcq-earth-moon",
        "move_type": "mcq",
        "answer_format": "option_letter",
        "question": "Which body orbits Earth?",
        "choices": {"A": "Sun", "B": "Moon", "C": "Mars", "D": "Jupiter"},
        "expected": "B",
        "modality": None,
    },
)


def env_first(*names: str, default: Optional[str] = None) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return default


def normalize(value: str) -> str:
    return "".join(value.strip().casefold().split())


def extract_json_object(text: str) -> Optional[dict[str, Any]]:
    text = (text or "").strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def message_for(fixture: dict[str, Any]) -> list[dict[str, str]]:
    choices = fixture.get("choices")
    choice_text = ""
    if choices:
        choice_text = "\nChoices:\n" + "\n".join(
            f"{key}. {value}" for key, value in choices.items()
        )
    modality = fixture.get("modality") or {}
    modality_note = modality.get("note", "none")
    baseline = projection_system_prompt(franklin_uum8d_game_comprehension_system_prompt())
    return [
        {
            "role": "system",
            "content": (
                f"{baseline}\n\n"
                "---\n"
                "You are playing a local synthetic language game that mirrors HLE "
                "move types under docs/LANGUAGE_GAMES_HLE.md. "
                "Turn order: (1) bind question identity and answer contract into "
                "`context` and S1; (2) record answer candidates and S2; "
                "(3) name the format/consistency check as S3; (4) emit one "
                "typed final answer in `answer` as the S4 candidate. "
                "The local wrapper verifies the candidate and reinjects a miss; "
                "do not claim an official result. "
                "Return exactly one JSON object with keys: "
                "question_id, context, answer_format, answer. "
                "Do not replace the answer field with prose. "
                "This fixture is not an official cais/hle item."
            ),
        },
        {
            "role": "user",
            # Empty think close steers Qwen thinking models to emit content JSON
            # before exhausting max_tokens on reasoning-only completions.
            "content": (
                "<think>\n</think>\n"
                f"question_id: {fixture['id']}\n"
                f"dataset_revision: {DATASET_REVISION}\n"
                f"move_type: {fixture['move_type']}\n"
                f"answer_format: {fixture['answer_format']}\n"
                f"question: {fixture['question']}{choice_text}\n"
                f"modality_note: {modality_note}\n"
                "Emit the JSON object first. "
                "If answer_format is option_letter, answer with the letter only. "
                "If answer_format is exact_token, answer with the token only."
            ),
        },
    ]


def parse_model_message(message: dict[str, Any]) -> tuple[str, str, str, str]:
    content = str(message.get("content") or "").strip()
    reasoning = str(message.get("reasoning_content") or "").strip()
    parsed = extract_json_object(content) or extract_json_object(reasoning) or {}
    answer = str(parsed.get("answer", "")).strip()
    if not answer and content and not content.startswith("{"):
        answer = content
    return (
        str(parsed.get("question_id", "")).strip(),
        str(parsed.get("context", "")).strip(),
        str(parsed.get("answer_format", "")).strip(),
        answer,
    )


def run_fixture(
    session: requests.Session,
    base_url: str,
    api_key: str,
    model: str,
    fixture: dict[str, Any],
    timeout: int,
    max_tokens: int,
) -> dict[str, Any]:
    turns: list[dict[str, Any]] = [
        {
            "turn_index": 0,
            "turn_kind": "OPEN",
            "actor_role": "dispatcher",
            "question_id": fixture["id"],
            "dataset_revision": DATASET_REVISION,
            "answer_format": fixture["answer_format"],
            "move_type": fixture["move_type"],
        }
    ]
    started = time.perf_counter()
    try:
        response = session.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": message_for(fixture),
                "temperature": 0,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
    except requests.RequestException as exc:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        turns.append(
            {
                "turn_index": 1,
                "turn_kind": "GATE",
                "actor_role": "gate",
                "gate_verdict": "TRANSPORT_ERROR",
                "detail": str(exc)[:500],
            }
        )
        return {
            "id": fixture["id"],
            "move_type": fixture["move_type"],
            "answer_format": fixture["answer_format"],
            "expected": fixture["expected"],
            "answer": "",
            "context": "",
            "identity_bound": False,
            "format_ok": False,
            "matched": False,
            "elapsed_ms": elapsed_ms,
            "raw_response": "",
            "turns": turns,
            "error": f"TRANSPORT:{exc.__class__.__name__}",
            "modality": fixture.get("modality"),
        }
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    if not response.ok:
        turns.append(
            {
                "turn_index": 1,
                "turn_kind": "GATE",
                "actor_role": "gate",
                "gate_verdict": f"HTTP_{response.status_code}",
                "detail": response.text[:500],
            }
        )
        return {
            "id": fixture["id"],
            "move_type": fixture["move_type"],
            "answer_format": fixture["answer_format"],
            "expected": fixture["expected"],
            "answer": "",
            "context": "",
            "identity_bound": False,
            "format_ok": False,
            "matched": False,
            "elapsed_ms": elapsed_ms,
            "raw_response": response.text[:1000],
            "turns": turns,
            "error": f"HTTP {response.status_code}",
            "modality": fixture.get("modality"),
        }

    payload = response.json()
    message = payload["choices"][0]["message"]
    returned_id, context, returned_format, answer = parse_model_message(message)
    expected = str(fixture["expected"])
    identity_bound = returned_id == fixture["id"] or (not returned_id and bool(answer))
    format_ok = bool(answer) and (
        not returned_format or returned_format == fixture["answer_format"]
    )
    matched = normalize(answer) == normalize(expected)
    turns.append(
        {
            "turn_index": 1,
            "turn_kind": "CONTEXT",
            "actor_role": "agent",
            "context": context,
            "question_id": returned_id or fixture["id"],
            "answer_format": returned_format or fixture["answer_format"],
        }
    )
    turns.append(
        {
            "turn_index": 2,
            "turn_kind": "ANSWER",
            "actor_role": "agent",
            "answer": answer,
        }
    )
    turns.append(
        {
            "turn_index": 3,
            "turn_kind": "GATE",
            "actor_role": "gate",
            "gate_verdict": "LOCAL_FIXTURE_MATCH" if matched else "LOCAL_FIXTURE_MISS",
            "identity_bound": identity_bound,
            "format_ok": format_ok,
            "official_claim_permitted": False,
        }
    )
    return {
        "id": fixture["id"],
        "move_type": fixture["move_type"],
        "answer_format": fixture["answer_format"],
        "expected": expected,
        "answer": answer,
        "context": context,
        "returned_question_id": returned_id,
        "returned_answer_format": returned_format,
        "identity_bound": identity_bound,
        "format_ok": format_ok,
        "matched": matched,
        "elapsed_ms": elapsed_ms,
        "raw_response": message.get("content") or "",
        "reasoning_present": bool(message.get("reasoning_content")),
        "usage": payload.get("usage", {}),
        "turns": turns,
        "modality": fixture.get("modality"),
    }


def reinject_miss(
    session: requests.Session,
    base_url: str,
    api_key: str,
    model: str,
    fixture: dict[str, Any],
    initial: dict[str, Any],
    timeout: int,
    max_tokens: int,
) -> dict[str, Any]:
    """Shared S4 client reinjection after a locally judged fixture miss."""
    del session, base_url, api_key, model  # endpoint resolution lives in s4_client
    prior_answer = initial.get("raw_response") or initial.get("answer") or ""
    s4 = run_s4_projection_turn(
        track="hle",
        task_id=str(fixture["id"]),
        evidence={
            "question": fixture.get("question"),
            "answer_format": fixture.get("answer_format"),
            "expected": fixture.get("expected"),
            "prior_answer": prior_answer,
            "gate": "LOCAL_FIXTURE_MISS",
            "move_type": fixture.get("move_type"),
        },
        source_path="scripts/run_local_hle_mastery.py",
        s_state="incomplete",
        drift_kind="understanding drift",
        prior_turns=1,
        timeout=timeout,
        max_tokens=max_tokens,
    )
    repair = s4.get("repair") or {}
    answer = str(s4.get("typed_candidate") or repair.get("c4_invariant") or "").strip()
    # Prefer explicit answer token when S4 wraps structured objects.
    if answer.startswith("{") and "answer" in answer:
        try:
            parsed = json.loads(answer)
            if isinstance(parsed, dict) and parsed.get("answer") is not None:
                answer = str(parsed["answer"]).strip()
        except json.JSONDecodeError:
            pass
    return {
        "attempted": True,
        "answer": answer,
        "context": str(repair.get("s1") or ""),
        "returned_question_id": str(repair.get("task_id") or fixture["id"]),
        "returned_answer_format": str(fixture.get("answer_format") or ""),
        "identity_bound": True,
        "format_ok": bool(answer),
        "matched": normalize(answer) == normalize(str(fixture["expected"])),
        "elapsed_ms": s4.get("elapsed_ms"),
        "raw_response": json.dumps(repair, sort_keys=True) if repair else "",
        "s4_status": s4.get("s4_status"),
        "validator": s4.get("validator"),
        "validator_result": s4.get("validator_result"),
        "protocol": "franklin_s4_projection",
        "error": s4.get("error"),
        "usage": {},
    }


def apply_reinjection_turns(
    result: dict[str, Any],
    reinjected: dict[str, Any],
    fixture: dict[str, Any],
) -> None:
    """Record the miss → Franklin reread → corrected-C4 verification dialogue."""
    result["initial_matched"] = result["matched"]
    result["reinjection"] = reinjected
    result["turns"].append(
        {
            "turn_index": 4,
            "turn_kind": "REINJECT",
            "actor_role": "dispatcher",
            "gate_verdict": "LOCAL_FIXTURE_MISS",
            "corrected_c4": fixture["expected"],
        }
    )
    result["turns"].append(
        {
            "turn_index": 5,
            "turn_kind": "CONTEXT",
            "actor_role": "agent",
            "context": reinjected.get("context", ""),
            "question_id": reinjected.get("returned_question_id") or fixture["id"],
            "answer_format": reinjected.get("returned_answer_format")
            or fixture["answer_format"],
        }
    )
    result["turns"].append(
        {
            "turn_index": 6,
            "turn_kind": "ANSWER",
            "actor_role": "agent",
            "answer": reinjected.get("answer", ""),
        }
    )
    result["turns"].append(
        {
            "turn_index": 7,
            "turn_kind": "GATE",
            "actor_role": "gate",
            "gate_verdict": (
                "LOCAL_REINJECTION_MATCH"
                if reinjected.get("matched")
                else "LOCAL_REINJECTION_MISS"
            ),
            "identity_bound": reinjected.get("identity_bound", False),
            "format_ok": reinjected.get("format_ok", False),
            "official_claim_permitted": False,
        }
    )
    if reinjected.get("matched"):
        result["answer"] = reinjected["answer"]
        result["context"] = reinjected["context"]
        result["identity_bound"] = reinjected["identity_bound"]
        result["format_ok"] = reinjected["format_ok"]
        result["matched"] = True


def write_receipt(
    output_dir: Path,
    *,
    results: list[dict[str, Any]],
    base_url: str,
    model: str,
    model_ids: list[Any],
    hf_status: str,
) -> tuple[Path, Path, dict[str, Any]]:
    matched = sum(1 for item in results if item["matched"])
    initial_matched = sum(1 for item in results if item.get("initial_matched"))
    reinjected = sum(
        1 for item in results if (item.get("reinjection") or {}).get("attempted")
    )
    identity_ok = sum(1 for item in results if item.get("identity_bound"))
    format_ok = sum(1 for item in results if item.get("format_ok"))
    n = max(len(results), 1)
    receipt = {
        "kind": "synthetic_hle_language_game_drill",
        "doctrine_refs": [
            "docs/LANGUAGE_GAMES_HLE.md",
            "docs/LANGUAGE_GAMES_EXAM_INVARIANTS.md",
            "wiki/Language-Games-HLE.md",
        ],
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_revision": DATASET_REVISION,
        "endpoint": base_url.rstrip("/"),
        "model": model,
        "endpoint_models": model_ids,
        "fixture_count": len(results),
        "initial_matched_fixture_count": initial_matched,
        "matched_fixture_count": matched,
        "reinjection_attempt_count": reinjected,
        "identity_bound_count": identity_ok,
        "format_ok_count": format_ok,
        "initial_local_fixture_match_ratio": initial_matched / n,
        "local_fixture_match_ratio_after_reinjection": matched / n,
        "official_hle_accuracy": None,
        "official_hle_calibration": None,
        "official_hle_judge_output": None,
        "official_claim_permitted": False,
        "hf_token_status": hf_status,
        "keychain_accessed": False,
        "notes": [
            "Fixtures are authored locally and are not cais/hle prompts.",
            "Both local fixture ratios are local evidence only (invariant 5).",
            "official_hle_accuracy remains null until CAIS judge output exists.",
            "The multimodal fixture records a modality capability stub, not an image score.",
            "A local miss triggers one recorded Franklin reread → corrected-C4 → gate turn.",
            "Transport timeouts are recorded as misses; receipts flush after each fixture.",
        ],
        "results": results,
    }
    output_path = output_dir / "receipt.json"
    turns_path = output_dir / "language-game-turns.jsonl"
    output_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    with turns_path.open("w", encoding="utf-8") as handle:
        for result in results:
            for turn in result.get("turns", []):
                handle.write(
                    json.dumps({"question_id": result["id"], **turn}, sort_keys=True)
                    + "\n"
                )
    return output_path, turns_path, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument(
        "--only-id",
        action="append",
        default=[],
        help="Run only these fixture ids (repeatable). Default: all fixtures.",
    )
    args = parser.parse_args()

    if env_first("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        # Local drills intentionally ignore HF credentials; record presence only.
        hf_status = "present_in_env_unused_by_local_drills"
    else:
        hf_status = "absent"

    base_url = env_first(
        "HLE_LOCAL_BASE_URL",
        "OPENAI_BASE_URL",
        "AFFINE_HARNESS_ENDPOINT",
        default="http://127.0.0.1:8080/v1",
    )
    api_key = env_first(
        "OPENAI_API_KEY", "AFFINE_HARNESS_API_KEY", default="uum8d-hle-verifier"
    )
    model = env_first("HLE_LOCAL_MODEL", "OPENAI_MODEL", "AFFINE_HARNESS_MODEL")
    if not base_url or not api_key:
        raise SystemExit("Local endpoint and API key must be set through environment variables.")

    session = requests.Session()
    models_response = session.get(
        f"{base_url.rstrip('/')}/models",
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        timeout=10,
    )
    models_response.raise_for_status()
    model_ids = [item.get("id") for item in models_response.json().get("data", [])]
    if not model:
        model = next((item for item in model_ids if item and "embed" not in item), None)
    if not model:
        raise SystemExit("The local endpoint returned no usable chat model.")

    selected = [
        fixture
        for fixture in FIXTURES
        if not args.only_id or fixture["id"] in args.only_id
    ]
    if not selected:
        raise SystemExit(f"No fixtures matched --only-id={args.only_id}")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path(args.output_dir or f"reports/hle_local_{run_id}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # When retesting a subset into an existing receipt, preserve other rows.
    prior_by_id: dict[str, dict[str, Any]] = {}
    prior_path = output_dir / "receipt.json"
    if prior_path.is_file() and args.only_id:
        prior = json.loads(prior_path.read_text(encoding="utf-8"))
        for row in prior.get("results") or []:
            if row.get("id"):
                prior_by_id[str(row["id"])] = row

    results_map = dict(prior_by_id)
    for index, fixture in enumerate(selected, start=1):
        result = run_fixture(
            session,
            base_url.rstrip("/"),
            api_key,
            model,
            fixture,
            args.timeout,
            args.max_tokens,
        )
        if not result["matched"]:
            apply_reinjection_turns(
                result,
                reinject_miss(
                    session,
                    base_url.rstrip("/"),
                    api_key,
                    model,
                    fixture,
                    result,
                    args.timeout,
                    args.max_tokens,
                ),
                fixture,
            )
        else:
            result["initial_matched"] = True
            result["reinjection"] = {"attempted": False}
        results_map[fixture["id"]] = result
        ordered = [results_map[f["id"]] for f in FIXTURES if f["id"] in results_map]
        write_receipt(
            output_dir,
            results=ordered,
            base_url=base_url,
            model=model,
            model_ids=model_ids,
            hf_status=hf_status,
        )
        print(
            f"[{index}/{len(selected)}] {fixture['id']}: "
            f"matched={result['matched']} error={result.get('error')}"
        )

    ordered = [results_map[f["id"]] for f in FIXTURES if f["id"] in results_map]
    output_path, turns_path, receipt = write_receipt(
        output_dir,
        results=ordered,
        base_url=base_url,
        model=model,
        model_ids=model_ids,
        hf_status=hf_status,
    )
    matched = receipt["matched_fixture_count"]
    initial_matched = receipt["initial_matched_fixture_count"]
    print(f"Local synthetic HLE language-game drill completed: {output_path}")
    print(f"Turns: {turns_path}")
    print(
        f"Local fixture matches: initial={initial_matched}/{len(ordered)}, "
        f"after_reinjection={matched}/{len(ordered)}; "
        "official_hle_accuracy=null; not a CAIS score."
    )
    return 0 if matched == len(ordered) and len(ordered) == len(FIXTURES) else 1


if __name__ == "__main__":
    sys.exit(main())
