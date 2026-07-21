"""Shared S¹–S⁴ evidence contract for Franklin language-game wrappers.

The fields are evidence states, not an assertion that a hidden answer is known.
An answer becomes locked only after the track-native verifier accepts it.
"""

from __future__ import annotations

from typing import Any, Mapping

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
