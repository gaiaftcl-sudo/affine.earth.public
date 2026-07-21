"""Shared Franklin S¹–S⁴ projection client for exam miss / mastery stuck paths.

All tracks (ARC-AGI-2, ARC-AGI-3, HLE) call the same two-way game:
wrapper evidence → typed S4 → local validator → LOCKED | REINJECT.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from llm_llvm_bench.arc.franklin_s4_projection import (
    S4_STATUS_LOCKED,
    S4_STATUS_REINJECT,
    default_validator_for_track,
)
from llm_llvm_bench.exam.miss_reinjection import (
    MissRecord,
    apply_local_s4_validator,
    build_franklin_messages,
    franklin_chat,
)


def run_s4_projection_turn(
    *,
    track: str,
    task_id: str,
    evidence: Mapping[str, Any],
    source_path: str = "shared_s4_client",
    s_state: str = "incomplete",
    drift_kind: str = "understanding drift",
    prior_turns: int = 0,
    timeout: int = 300,
    max_tokens: int = 1024,
) -> Dict[str, Any]:
    """One live Franklin S4 turn for a stuck task. Never dry-run. Never Kaggle."""
    miss = MissRecord(
        track=track,
        task_id=task_id,
        evidence=dict(evidence),
        source_path=source_path,
        s_state=s_state,
        drift_kind=drift_kind,
    )
    messages = build_franklin_messages(miss, prior_turns)
    frank = franklin_chat(messages, timeout=timeout, max_tokens=max_tokens, miss=miss)
    repair = frank.get("parsed")
    if isinstance(repair, dict):
        repair = apply_local_s4_validator(miss, repair)
    status = ""
    if isinstance(repair, dict):
        status = str(repair.get("s4_status") or "")
    return {
        "ok": bool(frank.get("ok")) and isinstance(repair, dict),
        "error": frank.get("error"),
        "track": track,
        "task_id": task_id,
        "s4_status": status,
        "typed_candidate": (repair or {}).get("typed_candidate") if repair else None,
        "validator": (repair or {}).get("validator")
        if repair
        else default_validator_for_track(track),
        "validator_result": (repair or {}).get("validator_result") if repair else {},
        "unresolved_alternatives": (repair or {}).get("unresolved_alternatives")
        if repair
        else [],
        "c4_invariant": (repair or {}).get("c4_invariant") if repair else "",
        "closure_ready": bool((repair or {}).get("closure_ready")) if repair else False,
        "repair": repair,
        "endpoint": frank.get("endpoint"),
        "model": frank.get("model"),
        "elapsed_ms": frank.get("elapsed_ms"),
        "fallback_used": frank.get("fallback_used"),
        "protocol": "franklin_s4_projection",
        "locked": status == S4_STATUS_LOCKED,
        "reinject": status == S4_STATUS_REINJECT,
    }


def maybe_run_s4_on_stuck(
    *,
    track: str,
    task_id: str,
    evidence: Mapping[str, Any],
    enabled: Optional[bool] = None,
    **kwargs: Any,
) -> Optional[Dict[str, Any]]:
    """Call S4 when EXAM_S4_ON_STUCK is not explicitly disabled (default on)."""
    import os

    if enabled is None:
        enabled = os.environ.get("EXAM_S4_ON_STUCK", "1") != "0"
    if not enabled:
        return None
    return run_s4_projection_turn(
        track=track, task_id=task_id, evidence=evidence, **kwargs
    )
