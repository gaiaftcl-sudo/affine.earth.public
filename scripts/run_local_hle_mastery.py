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

DATASET_REVISION = "local-synthetic-hle-fixtures-v1"

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
    return [
        {
            "role": "system",
            "content": (
                "You are playing a local synthetic language game that mirrors HLE "
                "move types under docs/LANGUAGE_GAMES_HLE.md. "
                "Turn order: (1) bind question identity and answer contract into "
                "`context`; (2) emit one typed final answer in `answer`. "
                "Return exactly one JSON object with keys: "
                "question_id, context, answer_format, answer. "
                "Do not replace the answer field with prose. "
                "This fixture is not an official cais/hle item."
            ),
        },
        {
            "role": "user",
            "content": (
                f"question_id: {fixture['id']}\n"
                f"dataset_revision: {DATASET_REVISION}\n"
                f"move_type: {fixture['move_type']}\n"
                f"answer_format: {fixture['answer_format']}\n"
                f"question: {fixture['question']}{choice_text}\n"
                f"modality_note: {modality_note}\n"
                "If answer_format is option_letter, answer with the letter only. "
                "If answer_format is exact_token, answer with the token only."
            ),
        },
    ]


def parse_model_message(message: dict[str, Any]) -> tuple[str, str, str, str]:
    content = str(message.get("content") or "").strip()
    reasoning = str(message.get("reasoning_content") or "").strip()
    parsed = extract_json_object(content) or extract_json_object(reasoning) or {}
    return (
        str(parsed.get("question_id", "")).strip(),
        str(parsed.get("context", "")).strip(),
        str(parsed.get("answer_format", "")).strip(),
        str(parsed.get("answer", "")).strip() or content,
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--max-tokens", type=int, default=2048)
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

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path(args.output_dir or f"reports/hle_local_{run_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    results = [
        run_fixture(
            session,
            base_url.rstrip("/"),
            api_key,
            model,
            fixture,
            args.timeout,
            args.max_tokens,
        )
        for fixture in FIXTURES
    ]
    matched = sum(1 for item in results if item["matched"])
    identity_ok = sum(1 for item in results if item["identity_bound"])
    format_ok = sum(1 for item in results if item["format_ok"])
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
        "matched_fixture_count": matched,
        "identity_bound_count": identity_ok,
        "format_ok_count": format_ok,
        "local_fixture_match_ratio": matched / len(results),
        "official_hle_accuracy": None,
        "official_hle_calibration": None,
        "official_hle_judge_output": None,
        "official_claim_permitted": False,
        "hf_token_status": hf_status,
        "keychain_accessed": False,
        "notes": [
            "Fixtures are authored locally and are not cais/hle prompts.",
            "local_fixture_match_ratio is local evidence only (invariant 5).",
            "official_hle_accuracy remains null until CAIS judge output exists.",
            "The multimodal fixture records a modality capability stub, not an image score.",
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
    print(f"Local synthetic HLE language-game drill completed: {output_path}")
    print(f"Turns: {turns_path}")
    print(
        f"Local fixture matches: {matched}/{len(results)}; "
        "official_hle_accuracy=null; not a CAIS score."
    )
    return 0 if matched == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
