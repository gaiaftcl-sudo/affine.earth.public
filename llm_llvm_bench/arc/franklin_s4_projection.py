"""Shared S¹–S⁴ evidence contract for Franklin language-game wrappers.

The fields are evidence states, not an assertion that a hidden answer is known.
An answer becomes locked only after the track-native verifier accepts it.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, MutableMapping, Optional, Sequence

S4_STATUS_LOCKED = "LOCKED"
S4_STATUS_REINJECT = "REINJECT"
S4_STATUSES = frozenset({S4_STATUS_LOCKED, S4_STATUS_REINJECT})

S4_PROJECTION_PROTOCOL = """\
Use a two-way evidence game, not a one-shot answer:
S1 (identity + complete ingestion): record task/question ID, revision, full
input, modality, and answer contract.
S2 (rule candidates): record every rule/answer candidate consistent with the
available demonstrations, observations, or prompt facts.
S3 (discriminating evidence): record the next legal probe, replay, citation,
or consistency check that distinguishes remaining candidates.
S4 (verified projection): record the typed candidate, the validator used, its
result, and unresolved alternatives. Emit LOCKED only when the task-native
validator accepts one candidate; otherwise emit REINJECT with the failed
evidence and next discriminating observation.

The wrapper supplies evidence, Franklin proposes or revises the typed C4
candidate, the wrapper validates it, and a miss is reinjected as a new turn.
Do not treat prose confidence, local transport, or an unavailable official
evaluator as an exact-match result."""

S4_RESPONSE_JSON_SCHEMA: dict[str, Any] = {
    "name": "franklin_s4_projection_response",
    "schema": {
        "type": "object",
        "additionalProperties": True,
        "properties": {
            "task_id": {"type": "string"},
            "track": {"type": "string"},
            "s1": {},
            "s2": {},
            "s3": {},
            "s4": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "typed_candidate": {},
                    "validator": {"type": "string"},
                    "status": {"type": "string", "enum": ["LOCKED", "REINJECT"]},
                    "unresolved_alternatives": {"type": "array"},
                    "validator_result": {},
                },
                "required": ["typed_candidate", "validator", "status"],
            },
            "typed_candidate": {},
            "validator": {"type": "string"},
            "status": {"type": "string", "enum": ["LOCKED", "REINJECT"]},
            "unresolved_alternatives": {"type": "array"},
            "grammar_update": {"type": "string"},
            "repair_kind": {
                "type": "string",
                "enum": ["grammar", "solver_hint", "context", "action_theory"],
            },
            "research_note": {"type": "string"},
            "closure_ready": {"type": "boolean"},
            "c4_invariant": {"type": "string"},
        },
        "required": ["task_id", "track", "s1", "s2", "s3"],
    },
}


def projection_system_prompt(base_prompt: str) -> str:
    """Append the shared operational protocol to Franklin's root instruction."""
    return f"{base_prompt.strip()}\n\n---\n{S4_PROJECTION_PROTOCOL}"


def wrapper_evidence(
    *,
    track: str,
    item_id: str,
    answer_contract: str,
    s1: Mapping[str, Any],
    s2: Mapping[str, Any],
    s3: Mapping[str, Any],
    prior_gate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a serializable wrapper turn without fabricating a verdict."""
    return {
        "turn_kind": "WRAPPER_EVIDENCE",
        "track": track,
        "item_id": item_id,
        "answer_contract": answer_contract,
        "s1": dict(s1),
        "s2": dict(s2),
        "s3": dict(s3),
        "prior_gate": dict(prior_gate or {}),
        "required_response": {
            "s4": {
                "typed_candidate": "<track-native answer>",
                "validator": "<replay/action/format/official judge>",
                "status": "LOCKED|REINJECT",
                "unresolved_alternatives": ["<candidate>"],
            }
        },
    }


def default_validator_for_track(track: str) -> str:
    mapping = {
        "arc2": "demonstration_replay",
        "arc3": "environment_step",
        "hle": "exact_format_check",
    }
    return mapping.get(track, "task_native_validator")


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _normalize_status(raw: Any) -> Optional[str]:
    if raw is None:
        return None
    text = str(raw).strip().upper()
    if text in S4_STATUSES:
        return text
    if text in {"LOCK", "CLOSED", "PASS", "ACCEPTED", "OK"}:
        return S4_STATUS_LOCKED
    if text in {"FAIL", "MISS", "OPEN", "HEALING", "REJECT", "REJECTED"}:
        return S4_STATUS_REINJECT
    return None


def s4_response_score(obj: Mapping[str, Any]) -> int:
    """Rank a candidate JSON object by how completely it matches the S4 contract."""
    keys = {str(k).lower() for k in obj}
    score = 0
    for key in ("typed_candidate", "validator", "status", "s4"):
        if key in keys:
            score += 3
    for key in ("s1", "s2", "s3", "unresolved_alternatives", "c4_invariant"):
        if key in keys:
            score += 2
    for key in ("task_id", "track", "grammar_update", "closure_ready", "repair_kind"):
        if key in keys:
            score += 1
    nested = obj.get("s4")
    if isinstance(nested, Mapping):
        score += s4_response_score(nested) // 2
    return score


def normalize_s4_response(
    parsed: Optional[Mapping[str, Any]],
    *,
    track: str,
    task_id: str,
) -> Optional[dict[str, Any]]:
    """Coerce Franklin JSON into the canonical LOCKED|REINJECT S4 repair shape."""
    if not isinstance(parsed, dict):
        return None

    working: MutableMapping[str, Any] = dict(parsed)
    for nest_key in ("repair", "result", "payload", "json", "data", "answer", "s4_response"):
        nested = working.get(nest_key)
        if isinstance(nested, dict) and s4_response_score(nested) >= s4_response_score(working):
            working = dict(nested)
            break

    s4_obj = working.get("s4")
    if isinstance(s4_obj, dict):
        flat = dict(working)
        for key in (
            "typed_candidate",
            "validator",
            "status",
            "unresolved_alternatives",
            "validator_result",
        ):
            if key not in flat and key in s4_obj:
                flat[key] = s4_obj[key]
        # Keep prose s4 acceptance text if present as a non-object.
        working = flat
    elif isinstance(s4_obj, str) and s4_obj.strip():
        # Legacy string s4 — keep as acceptance note.
        pass

    def pick(*names: str) -> Any:
        lower_map = {str(k).lower(): v for k, v in working.items()}
        for name in names:
            if name.lower() in lower_map and lower_map[name.lower()] not in (None, ""):
                return lower_map[name.lower()]
        return None

    s1 = pick("s1", "objects", "symbols", "ingestion")
    s2 = pick("s2", "relations", "candidates")
    s3 = pick("s3", "transforms", "actions", "legal_transforms", "discriminator")
    typed = pick(
        "typed_candidate",
        "candidate",
        "c4_invariant",
        "c4",
        "answer",
        "grid",
        "action",
        "projection",
    )
    validator = pick("validator", "named_validator", "check") or default_validator_for_track(
        track
    )
    status = _normalize_status(pick("status", "s4_status", "gate", "verdict"))
    alternatives = _as_list(
        pick("unresolved_alternatives", "alternatives", "remaining_candidates")
    )
    grammar = pick("grammar_update", "grammar", "update", "repair")
    repair_kind = pick("repair_kind", "kind") or "grammar"
    note = pick("research_note", "note", "rationale") or ""
    closure = pick("closure_ready", "ready", "closed")
    validator_result = pick("validator_result", "gate_result", "check_result")

    # Legacy path: string s4 + c4 without explicit status.
    legacy_s4 = pick("s4", "acceptance", "acceptance_boundary", "boundary")
    if status is None:
        if isinstance(closure, str) and closure.strip().lower() in {"1", "true", "yes", "ready"}:
            status = S4_STATUS_LOCKED
        elif closure is True:
            status = S4_STATUS_LOCKED
        elif typed or legacy_s4 or grammar:
            status = S4_STATUS_REINJECT
        else:
            return None

    if isinstance(closure, str):
        closure_ready = closure.strip().lower() in {"1", "true", "yes", "ready"}
    elif closure is None:
        closure_ready = status == S4_STATUS_LOCKED
    else:
        closure_ready = bool(closure)

    if status == S4_STATUS_LOCKED and not _as_text(typed).strip():
        # Empty LOCKED is invalid — force disciplined REINJECT.
        status = S4_STATUS_REINJECT
        closure_ready = False

    if _as_text(s1) == "DRY_RUN" or _as_text(typed) == "DRY_RUN":
        return None

    s4_summary = {
        "typed_candidate": typed if typed is not None else "",
        "validator": _as_text(validator),
        "status": status,
        "unresolved_alternatives": alternatives,
        "validator_result": validator_result if isinstance(validator_result, dict) else {},
    }

    repair = {
        "task_id": _as_text(pick("task_id", "id") or task_id),
        "track": _as_text(pick("track") or track),
        "s1": _as_text(s1) if s1 is not None else "",
        "s2": _as_text(s2) if s2 is not None else "",
        "s3": _as_text(s3) if s3 is not None else "",
        "s4": _as_text(legacy_s4) if isinstance(legacy_s4, str) else json.dumps(s4_summary, sort_keys=True),
        "s4_status": status,
        "typed_candidate": typed if typed is not None else "",
        "validator": _as_text(validator),
        "unresolved_alternatives": alternatives,
        "validator_result": s4_summary["validator_result"],
        "c4_invariant": _as_text(typed) if typed is not None else "",
        "grammar_update": _as_text(grammar),
        "repair_kind": _as_text(repair_kind),
        "research_note": _as_text(note),
        "closure_ready": bool(closure_ready) and status == S4_STATUS_LOCKED,
    }
    if not (repair["s1"] or repair["c4_invariant"] or repair["grammar_update"] or repair["s4_status"]):
        return None
    return repair


def build_miss_wrapper_evidence(
    *,
    track: str,
    task_id: str,
    s_state: str,
    drift_kind: str,
    evidence: Mapping[str, Any],
    prior_turns: int,
    prior_gate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build WRAPPER_EVIDENCE for an exam miss reinjection turn."""
    contracts = {
        "arc2": "typed output grid; LOCKED only after demonstration_replay accepts",
        "arc3": "legal next action/trajectory; LOCKED only after environment_step accepts",
        "hle": "typed answer token/letter; LOCKED only after exact_format_check accepts",
    }
    return wrapper_evidence(
        track=track,
        item_id=task_id,
        answer_contract=contracts.get(track, "track-native typed candidate"),
        s1={
            "task_id": task_id,
            "track": track,
            "s_state": s_state,
            "ingestion": "miss_receipt",
            "evidence_keys": sorted(str(k) for k in evidence.keys())[:40],
        },
        s2={
            "drift_kind": drift_kind,
            "rule_candidates": "enumerate every demonstration-consistent candidate",
            "prior_turns": prior_turns,
        },
        s3={
            "discriminator": default_validator_for_track(track),
            "next_probe": "emit one typed candidate the named validator can accept or reject",
        },
        prior_gate=prior_gate,
    )


def exam_s4_user_prompt(evidence_turn: Mapping[str, Any], miss_evidence_json: str) -> str:
    """User content that forces the LOCKED|REINJECT JSON shape."""
    return (
        "WRAPPER_EVIDENCE follows. Reply with ONE compact JSON object only — no "
        "markdown fences, no prose outside JSON, no chain-of-thought in fields.\n"
        "Required top-level keys: task_id, track, s1, s2, s3, s4, grammar_update, "
        "repair_kind, research_note, closure_ready.\n"
        "s1,s2,s3 MUST be short strings (≤160 chars each), not essays.\n"
        "s4 MUST be an object with keys: typed_candidate, validator, status, "
        "unresolved_alternatives (≤3 short strings).\n"
        "typed_candidate MUST be a short rule string or small grid — never dump "
        "full 29×29 grids into JSON.\n"
        "status MUST be exactly LOCKED or REINJECT.\n"
        "closure_ready is true only when status is LOCKED.\n"
        f"wrapper_evidence={json.dumps(evidence_turn, sort_keys=True)}\n"
        f"miss_evidence={miss_evidence_json}\n"
        "Emit the JSON object now."
    )
