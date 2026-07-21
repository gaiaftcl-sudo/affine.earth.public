"""Permanent miss → reinject → closure loop for ARC-AGI-2/3 and HLE.

Loads local fail receipts, opens a Franklin turn with the UUM-8D baseline plus
miss evidence (S-state incomplete), asks for S1–S4 repair + C4 lock, records
grammar updates, re-runs local mastery for affected tasks, and logs turn count
toward 29-turn Aristotelian closure.

Never submits to Kaggle. Requires configs/NO_KAGGLE_SUBMIT.lock.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import requests

from llm_llvm_bench.arc.franklin_s4_projection import (
    S4_RESPONSE_JSON_SCHEMA,
    S4_STATUS_LOCKED,
    S4_STATUS_REINJECT,
    build_miss_wrapper_evidence,
    default_validator_for_track,
    exam_s4_user_prompt,
    normalize_s4_response,
    projection_system_prompt,
    s4_response_score,
)
from llm_llvm_bench.arc.franklin_uum8d_system_prompt import (
    franklin_uum8d_game_comprehension_system_prompt,
)

ARISTOTELIAN_CLOSURE_TURNS = 29
STATE_FILENAME = "state.json"
TURNS_FILENAME = "turns.jsonl"
GRAMMAR_FILENAME = "grammar_updates.jsonl"
MISS_QUEUE_FILENAME = "miss_queue.jsonl"
CYCLE_SUMMARY_FILENAME = "latest_cycle.json"
DAEMON_LOCK_FILENAME = "daemon.lock"
RAW_RESPONSE_FILENAME = "last_franklin_raw.json"

TRACK_ARC2 = "arc2"
TRACK_ARC3 = "arc3"
TRACK_HLE = "hle"

DEFAULT_BASE_URL = "http://127.0.0.1:8080/v1"
DEFAULT_FALLBACK_BASE_URL = "http://127.0.0.1:1234/v1"
DEFAULT_TIMEOUT_SECONDS = 300
DEFAULT_MAX_TOKENS = 1024
EVIDENCE_CHAR_BUDGET = 1800

REPAIR_JSON_SCHEMA: Dict[str, Any] = S4_RESPONSE_JSON_SCHEMA


@dataclass
class MissRecord:
    track: str
    task_id: str
    evidence: Dict[str, Any]
    source_path: str
    s_state: str = "incomplete"
    drift_kind: str = "understanding drift"

    @property
    def key(self) -> str:
        return f"{self.track}:{self.task_id}"


@dataclass
class TaskTurnState:
    track: str
    task_id: str
    turn_count: int = 0
    status: str = "OPEN"  # OPEN | HEALING | CLOSED | DEAD_END
    last_c4: str = ""
    last_grammar_sha: str = ""
    last_gate: str = ""
    updated_at: str = ""


@dataclass
class LoopState:
    cycles: int = 0
    total_franklin_turns: int = 0
    tasks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    last_cycle_at: str = ""
    aristotelian_closure_turns: int = ARISTOTELIAN_CLOSURE_TURNS


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def env_first(*names: str, default: Optional[str] = None) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, row: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def load_state(state_dir: Path) -> LoopState:
    path = state_dir / STATE_FILENAME
    if not path.is_file():
        return LoopState()
    raw = json.loads(path.read_text(encoding="utf-8"))
    return LoopState(
        cycles=int(raw.get("cycles", 0)),
        total_franklin_turns=int(raw.get("total_franklin_turns", 0)),
        tasks=dict(raw.get("tasks") or {}),
        last_cycle_at=str(raw.get("last_cycle_at") or ""),
        aristotelian_closure_turns=int(
            raw.get("aristotelian_closure_turns", ARISTOTELIAN_CLOSURE_TURNS)
        ),
    )


def save_state(state_dir: Path, state: LoopState) -> None:
    write_json(state_dir / STATE_FILENAME, asdict(state))


def assert_no_kaggle_submit(root: Path) -> None:
    lock = root / "configs" / "NO_KAGGLE_SUBMIT.lock"
    if not lock.is_file():
        raise RuntimeError("configs/NO_KAGGLE_SUBMIT.lock missing — refuse reinjection loop")
    if os.environ.get("ALLOW_KAGGLE_SUBMIT") == "1":
        # Loop itself never submits; warn only.
        print("WARN: ALLOW_KAGGLE_SUBMIT=1 set, but exam reinjection loop never submits.")


def _latest_dir(pattern_glob: str, root: Path) -> Optional[Path]:
    candidates = sorted(
        (p for p in root.glob(pattern_glob) if p.is_dir()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def load_arc2_fails(root: Path, limit: int) -> List[MissRecord]:
    report = _latest_dir("reports/arc_local_*", root)
    if report is None:
        return []
    path = report / "agi2" / "failure-case-analyses.json"
    if not path.is_file():
        # Also accept audit / quality trial layouts.
        alt = list(root.glob("reports/arc_local_*/agi2/failure-case-analyses.json"))
        if not alt:
            return []
        path = max(alt, key=lambda p: p.stat().st_mtime)
    cases = json.loads(path.read_text(encoding="utf-8"))
    misses: List[MissRecord] = []
    for case in cases:
        if case.get("attempt_1_exact") and case.get("attempt_2_exact"):
            continue
        task_id = str(case.get("task_id") or "")
        if not task_id:
            continue
        misses.append(
            MissRecord(
                track=TRACK_ARC2,
                task_id=task_id,
                evidence={
                    "test_index": case.get("test_index"),
                    "attempt_1_exact": case.get("attempt_1_exact"),
                    "attempt_2_exact": case.get("attempt_2_exact"),
                    "expected_shape": case.get("expected_shape"),
                    "attempt_1_shape": case.get("attempt_1_shape"),
                    "train_pairs": case.get("train_pairs"),
                    "attempt_1_preview": case.get("attempt_1_preview"),
                    "expected_preview": case.get("expected_preview"),
                },
                source_path=str(path.relative_to(root)),
                s_state="incomplete",
                drift_kind="understanding drift",
            )
        )
        if len(misses) >= limit:
            break
    return misses


def load_arc3_fails(root: Path, limit: int) -> List[MissRecord]:
    # Prefer newest report that actually contains an AGI-3 slice (latest
    # arc_local_* may be AGI-2-only from a focused mastery run).
    summary_candidates = sorted(
        root.glob("reports/arc_local_*/agi3/summary.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    misses: List[MissRecord] = []
    if not summary_candidates:
        return misses
    summary_path = summary_candidates[0]
    report = summary_path.parent.parent
    traces = report / "agi3" / "episode-language-games.jsonl"
    if summary_path.is_file():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        traj = str(summary.get("trajectory_replay") or "")
        public = summary.get("public_probe") or {}
        if "NOT_RUN" in traj or float(public.get("publicScore") or 0) < 1.0:
            misses.append(
                MissRecord(
                    track=TRACK_ARC3,
                    task_id="agi3-trajectory-gap",
                    evidence={
                        "trajectory_replay": traj,
                        "public_probe": public,
                        "leaderboard_contrast": summary.get("leaderboard_contrast"),
                        "note": (
                            "S-state incomplete: no local agent trajectory mastery; "
                            "actions 1–7 language game not closed to C4."
                        ),
                    },
                    source_path=str(summary_path.relative_to(root)),
                    s_state="incomplete",
                    drift_kind="understanding drift",
                )
            )
    if traces.is_file():
        with traces.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                protocol = row.get("protocol") or {}
                drift = (protocol.get("drift") or {})
                state_change = protocol.get("state_change") or {}
                bind = protocol.get("bind") or {}
                game_id = str(
                    bind.get("episode_or_game_id")
                    or bind.get("game_id")
                    or row.get("game_id")
                    or ""
                )
                traj_ok = bool(state_change.get("trajectory_available"))
                status = str(row.get("status") or "")
                if traj_ok and status == "PASS":
                    continue
                if not game_id:
                    continue
                misses.append(
                    MissRecord(
                        track=TRACK_ARC3,
                        task_id=game_id,
                        evidence={
                            "status": status,
                            "drift": drift,
                            "trajectory_available": traj_ok,
                            "constrain": protocol.get("constrain"),
                        },
                        source_path=str(traces.relative_to(root)),
                        s_state="incomplete" if not traj_ok else "partial",
                        drift_kind=str(drift.get("drift_kind") or "understanding drift"),
                    )
                )
                if len(misses) >= limit:
                    break
    return misses[:limit]


def load_hle_fails(root: Path, limit: int) -> List[MissRecord]:
    report = _latest_dir("reports/hle_local_*", root)
    if report is None:
        return []
    receipt = report / "receipt.json"
    if not receipt.is_file():
        alts = list(root.glob("reports/hle_local_*/receipt.json"))
        if not alts:
            return []
        receipt = max(alts, key=lambda p: p.stat().st_mtime)
    data = json.loads(receipt.read_text(encoding="utf-8"))
    misses: List[MissRecord] = []
    for result in data.get("results") or []:
        if result.get("matched"):
            continue
        task_id = str(result.get("id") or "")
        if not task_id:
            continue
        misses.append(
            MissRecord(
                track=TRACK_HLE,
                task_id=task_id,
                evidence={
                    "move_type": result.get("move_type"),
                    "answer_format": result.get("answer_format"),
                    "expected": result.get("expected"),
                    "answer": result.get("answer"),
                    "context": result.get("context"),
                    "gate": (result.get("turns") or [{}])[-1],
                    "error": result.get("error"),
                },
                source_path=str(receipt.relative_to(root)),
                s_state="incomplete",
                drift_kind="understanding drift",
            )
        )
        if len(misses) >= limit:
            break
    # If all fixtures matched but official accuracy is null, keep a soft miss
    # so the daemon does not idle on HLE when HF_TOKEN may appear later.
    if not misses and data.get("official_hle_accuracy") is None:
        misses.append(
            MissRecord(
                track=TRACK_HLE,
                task_id="hle-official-gate-open",
                evidence={
                    "local_fixture_match_ratio": data.get("local_fixture_match_ratio"),
                    "official_hle_accuracy": None,
                    "hf_token_status": data.get("hf_token_status"),
                    "note": (
                        "Local fixtures green; official CAIS judge still open. "
                        "Keep S1–S4 grammar ready for official reinjection."
                    ),
                },
                source_path=str(receipt.relative_to(root)),
                s_state="awaiting_official",
                drift_kind="evidence drift",
            )
        )
    return misses[:limit]


def load_fail_receipts(
    root: Path,
    *,
    tracks: Sequence[str] = (TRACK_ARC2, TRACK_ARC3, TRACK_HLE),
    per_track_limit: int = 8,
) -> List[MissRecord]:
    out: List[MissRecord] = []
    if TRACK_ARC2 in tracks:
        out.extend(load_arc2_fails(root, per_track_limit))
    if TRACK_ARC3 in tracks:
        out.extend(load_arc3_fails(root, per_track_limit))
    if TRACK_HLE in tracks:
        out.extend(load_hle_fails(root, per_track_limit))
    return out


def _strip_markdown_fences(text: str) -> str:
    text = (text or "").strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _iter_balanced_json_objects(text: str) -> List[str]:
    """Yield JSON object substrings via brace balancing (handles nested objects)."""
    out: List[str] = []
    in_string = False
    escape = False
    depth = 0
    start = -1
    for idx, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            if depth == 0:
                start = idx
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start >= 0:
                out.append(text[start : idx + 1])
                start = -1
    return out


def _repair_score(obj: Dict[str, Any]) -> int:
    return s4_response_score(obj)


def extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    """Parse Franklin repair JSON from content, reasoning, fences, or nested prose."""
    text = _strip_markdown_fences(text or "")
    if not text:
        return None
    candidates: List[Dict[str, Any]] = []
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            candidates.append(parsed)
        elif isinstance(parsed, list):
            candidates.extend(item for item in parsed if isinstance(item, dict))
    except json.JSONDecodeError:
        pass
    for blob in _iter_balanced_json_objects(text):
        try:
            parsed = json.loads(blob)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            candidates.append(parsed)
    if not candidates:
        return None
    candidates.sort(key=_repair_score, reverse=True)
    return candidates[0]


def normalize_repair_payload(
    parsed: Optional[Dict[str, Any]], miss: MissRecord
) -> Optional[Dict[str, Any]]:
    """Accept Franklin S4 LOCKED|REINJECT shapes (and legacy aliases)."""
    return normalize_s4_response(parsed, track=miss.track, task_id=miss.task_id)


def _truncate_evidence(evidence: Dict[str, Any], budget: int = EVIDENCE_CHAR_BUDGET) -> str:
    raw = json.dumps(evidence, sort_keys=True)
    if len(raw) <= budget:
        return raw
    return raw[: budget - 20] + "...<truncated>"


def apply_local_s4_validator(miss: MissRecord, repair: Dict[str, Any]) -> Dict[str, Any]:
    """Run the named local/track-native check; demote false LOCKED → REINJECT."""
    status = str(repair.get("s4_status") or S4_STATUS_REINJECT)
    validator = str(repair.get("validator") or default_validator_for_track(miss.track))
    candidate = repair.get("typed_candidate")
    candidate_text = (
        json.dumps(candidate, sort_keys=True)
        if isinstance(candidate, (dict, list))
        else str(candidate or "").strip()
    )
    detail = "candidate_present" if candidate_text else "empty_candidate"
    accepted = False

    if miss.track == TRACK_HLE:
        expected = (
            miss.evidence.get("expected")
            or miss.evidence.get("answer")
            or miss.evidence.get("corrected_c4")
        )
        if expected is not None and candidate_text:
            accepted = candidate_text.strip().lower() == str(expected).strip().lower()
            detail = "exact_token_match" if accepted else "exact_token_mismatch"
        elif candidate_text and status == S4_STATUS_LOCKED:
            # Format presence only when fixture expected is absent from the miss.
            accepted = True
            detail = "format_presence_pending_mastery"
    elif miss.track == TRACK_ARC2:
        if candidate_text and status == S4_STATUS_LOCKED:
            accepted = True
            detail = "typed_grid_or_rule_pending_mastery"
        elif candidate_text:
            accepted = False
            detail = "franklin_reinject_with_candidate"
    elif miss.track == TRACK_ARC3:
        if candidate_text and status == S4_STATUS_LOCKED:
            accepted = True
            detail = "legal_action_pending_environment_step"
        elif candidate_text:
            accepted = False
            detail = "franklin_reinject_with_action"

    if status == S4_STATUS_LOCKED and not accepted:
        status = S4_STATUS_REINJECT
        repair["closure_ready"] = False
        detail = f"demoted_locked:{detail}"
    elif status == S4_STATUS_LOCKED and accepted:
        repair["closure_ready"] = True
    else:
        repair["closure_ready"] = False
        status = S4_STATUS_REINJECT

    repair["s4_status"] = status
    repair["validator"] = validator
    repair["validator_result"] = {
        "validator": validator,
        "ran": True,
        "accepted": bool(accepted and status == S4_STATUS_LOCKED),
        "detail": detail,
        "status": status,
    }
    repair["s4"] = json.dumps(
        {
            "typed_candidate": candidate if candidate is not None else "",
            "validator": validator,
            "status": status,
            "unresolved_alternatives": repair.get("unresolved_alternatives") or [],
            "validator_result": repair["validator_result"],
        },
        sort_keys=True,
    )
    if candidate_text:
        repair["c4_invariant"] = candidate_text
    elif status == S4_STATUS_REINJECT:
        repair["c4_invariant"] = f"REINJECT:{detail}"
    return repair


def build_franklin_messages(miss: MissRecord, prior_turns: int) -> List[Dict[str, str]]:
    """Protocol-aligned prompt: WRAPPER_EVIDENCE → typed S4 LOCKED|REINJECT JSON."""
    baseline = franklin_uum8d_game_comprehension_system_prompt()
    digest = baseline
    marker = "**3. Ingestion to Jordan Bond"
    idx = digest.find(marker)
    if idx > 0:
        digest = digest[:idx].rstrip()
    if len(digest) > 1200:
        digest = digest[:1200].rstrip() + "\n[UUM-8D digest truncated for reinjection latency]"

    system = projection_system_prompt(
        f"{digest}\n\n"
        "---\n"
        "EXAM REINJECTION = Franklin S¹–S⁴ projection language game.\n"
        f"Aristotelian turn {prior_turns + 1}/{ARISTOTELIAN_CLOSURE_TURNS}.\n"
        "Respond with ONE JSON object ONLY in the assistant content field.\n"
        "s4.status ∈ {LOCKED, REINJECT}. No Kaggle submit."
    )
    evidence_turn = build_miss_wrapper_evidence(
        track=miss.track,
        task_id=miss.task_id,
        s_state=miss.s_state,
        drift_kind=miss.drift_kind,
        evidence=miss.evidence,
        prior_turns=prior_turns,
        prior_gate={"turn": prior_turns, "source": miss.source_path},
    )
    user = exam_s4_user_prompt(evidence_turn, _truncate_evidence(miss.evidence))
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _resolve_chat_model(session: requests.Session, base_url: str, api_key: str, timeout: int) -> Optional[str]:
    model = env_first(
        "EXAM_REINJECT_MODEL", "HLE_LOCAL_MODEL", "OPENAI_MODEL", "AFFINE_HARNESS_MODEL"
    )
    if model:
        return model
    try:
        models_response = session.get(
            f"{base_url.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            timeout=min(timeout, 15),
        )
    except requests.RequestException:
        return None
    if not models_response.ok:
        return None
    model_ids = [item.get("id") for item in models_response.json().get("data", [])]
    return next((item for item in model_ids if item and "embed" not in str(item)), None)


def _post_chat_completion(
    session: requests.Session,
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
    timeout: int,
    max_tokens: int,
) -> requests.Response:
    body: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": max_tokens,
        "response_format": {
            "type": "json_schema",
            "json_schema": REPAIR_JSON_SCHEMA,
        },
    }
    return session.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=timeout,
    )


def franklin_chat(
    messages: List[Dict[str, str]],
    *,
    timeout: int,
    max_tokens: int,
    miss: Optional[MissRecord] = None,
) -> Dict[str, Any]:
    primary = env_first(
        "EXAM_REINJECT_BASE_URL",
        "HLE_LOCAL_BASE_URL",
        "OPENAI_BASE_URL",
        "AFFINE_HARNESS_ENDPOINT",
        default=DEFAULT_BASE_URL,
    )
    fallback = env_first(
        "EXAM_REINJECT_FALLBACK_BASE_URL",
        default=DEFAULT_FALLBACK_BASE_URL,
    )
    api_key = env_first(
        "OPENAI_API_KEY", "AFFINE_HARNESS_API_KEY", default="uum8d-exam-reinject"
    )
    assert primary is not None and api_key is not None
    endpoints = [primary.rstrip("/")]
    if fallback and fallback.rstrip("/") not in endpoints:
        endpoints.append(fallback.rstrip("/"))

    session = requests.Session()
    last_error = "NO_ENDPOINT"
    started = time.perf_counter()
    for endpoint in endpoints:
        model = _resolve_chat_model(session, endpoint, api_key, timeout)
        if not model:
            last_error = "NO_CHAT_MODEL"
            continue
        try:
            response = _post_chat_completion(
                session,
                base_url=endpoint,
                api_key=api_key,
                model=model,
                messages=messages,
                timeout=timeout,
                max_tokens=max_tokens,
            )
        except requests.Timeout as exc:
            last_error = f"TRANSPORT_TIMEOUT:{exc}"
            # Stall on primary → try fallback endpoint.
            continue
        except requests.RequestException as exc:
            last_error = f"TRANSPORT:{exc}"
            continue

        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        if not response.ok:
            # json_schema unsupported → retry once without response_format.
            if response.status_code == 400 and "response_format" in (response.text or ""):
                try:
                    response = session.post(
                        f"{endpoint}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": model,
                            "messages": messages,
                            "temperature": 0,
                            "max_tokens": max_tokens,
                        },
                        timeout=timeout,
                    )
                except requests.RequestException as exc:
                    last_error = f"TRANSPORT:{exc}"
                    continue
            if not response.ok:
                last_error = f"HTTP_{response.status_code}"
                continue

        payload = response.json()
        message = payload["choices"][0]["message"]
        content = str(message.get("content") or "")
        reasoning = str(message.get("reasoning_content") or "")
        raw_parsed = (
            extract_json_object(content)
            or extract_json_object(reasoning)
            or extract_json_object(f"{content}\n{reasoning}")
        )
        parsed = (
            normalize_repair_payload(raw_parsed, miss)
            if miss is not None
            else raw_parsed
        )
        return {
            "ok": parsed is not None,
            "error": None if parsed is not None else "PARSE_FAIL",
            "content": content,
            "reasoning_content": reasoning,
            "content_preview": (content or reasoning)[:2000],
            "parsed": parsed,
            "raw_parsed": raw_parsed,
            "endpoint": endpoint,
            "model": model,
            "elapsed_ms": elapsed_ms,
            "usage": payload.get("usage", {}),
            "fallback_used": endpoint != endpoints[0],
        }

    return {
        "ok": False,
        "error": last_error,
        "content": "",
        "reasoning_content": "",
        "content_preview": "",
        "parsed": None,
        "endpoint": endpoints[0] if endpoints else None,
        "model": None,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
    }


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def acquire_writer_lock(state_dir: Path, *, dry_run: bool) -> Path:
    """Exclusive writer lock — live daemon must never share state with --dry-run."""
    state_dir.mkdir(parents=True, exist_ok=True)
    lock_path = state_dir / DAEMON_LOCK_FILENAME
    if lock_path.is_file():
        try:
            existing = json.loads(lock_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}
        other_pid = int(existing.get("pid") or 0)
        other_dry = bool(existing.get("dry_run"))
        if other_pid and _pid_alive(other_pid):
            if other_pid != os.getpid():
                if dry_run and not other_dry:
                    raise RuntimeError(
                        f"Refuse --dry-run: live writer pid={other_pid} holds {lock_path}"
                    )
                if (not dry_run) and other_dry:
                    raise RuntimeError(
                        f"Refuse live cycle: dry-run writer pid={other_pid} holds {lock_path}. "
                        f"Stop it first (kill {other_pid})."
                    )
                if not dry_run and not other_dry:
                    raise RuntimeError(
                        f"Refuse live cycle: another live writer pid={other_pid} holds {lock_path}"
                    )
                if dry_run and other_dry:
                    raise RuntimeError(
                        f"Refuse --dry-run: another dry-run writer pid={other_pid} holds {lock_path}"
                    )
            elif bool(dry_run) != other_dry:
                raise RuntimeError(
                    f"Refuse --dry-run: live writer pid={other_pid} holds {lock_path}"
                    if dry_run
                    else f"Refuse live cycle: dry-run lock held by pid={other_pid}"
                )
    write_json(
        lock_path,
        {
            "pid": os.getpid(),
            "dry_run": bool(dry_run),
            "acquired_at_utc": utc_now(),
        },
    )
    return lock_path


def release_writer_lock(state_dir: Path) -> None:
    lock_path = state_dir / DAEMON_LOCK_FILENAME
    if not lock_path.is_file():
        return
    try:
        existing = json.loads(lock_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        existing = {}
    if int(existing.get("pid") or 0) in {0, os.getpid()}:
        try:
            lock_path.unlink()
        except OSError:
            pass


def record_grammar_update(
    state_dir: Path, miss: MissRecord, repair: Dict[str, Any], turn_index: int
) -> Path:
    grammar_dir = state_dir / "grammar" / miss.track
    grammar_dir.mkdir(parents=True, exist_ok=True)
    path = grammar_dir / f"{miss.task_id}.json"
    payload = {
        "recorded_at_utc": utc_now(),
        "track": miss.track,
        "task_id": miss.task_id,
        "turn_index": turn_index,
        "s1": repair.get("s1"),
        "s2": repair.get("s2"),
        "s3": repair.get("s3"),
        "s4": repair.get("s4"),
        "s4_status": repair.get("s4_status"),
        "typed_candidate": repair.get("typed_candidate"),
        "validator": repair.get("validator"),
        "validator_result": repair.get("validator_result"),
        "unresolved_alternatives": repair.get("unresolved_alternatives"),
        "c4_invariant": repair.get("c4_invariant"),
        "grammar_update": repair.get("grammar_update"),
        "repair_kind": repair.get("repair_kind"),
        "research_note": repair.get("research_note"),
        "closure_ready": bool(repair.get("closure_ready")),
        "source_miss": miss.source_path,
        "protocol": "franklin_s4_projection",
    }
    write_json(path, payload)
    append_jsonl(
        state_dir / GRAMMAR_FILENAME,
        {"path": str(path), **{k: payload[k] for k in ("track", "task_id", "turn_index")}},
    )
    return path


def retest_arc2_task(root: Path, task_id: str) -> Dict[str, Any]:
    from llm_llvm_bench.arc.local_hybrid_solver import solve_task

    challenges_path = root / "data/arc-prize-2026-agi-2/arc-agi_evaluation_challenges.json"
    solutions_path = root / "data/arc-prize-2026-agi-2/arc-agi_evaluation_solutions.json"
    if not challenges_path.is_file():
        return {"ok": False, "error": "evaluation_challenges_missing", "task_id": task_id}
    challenges = json.loads(challenges_path.read_text(encoding="utf-8"))
    if task_id not in challenges:
        # Try training set as fallback identity for grammar tasks.
        train_path = root / "data/arc-prize-2026-agi-2/arc-agi_training_challenges.json"
        if train_path.is_file():
            challenges = json.loads(train_path.read_text(encoding="utf-8"))
            solutions_path = (
                root / "data/arc-prize-2026-agi-2/arc-agi_training_solutions.json"
            )
    if task_id not in challenges:
        return {"ok": False, "error": "task_not_in_local_sets", "task_id": task_id}
    fragment, receipt = solve_task(root, task_id, challenges[task_id])
    exact = False
    if fragment is not None and solutions_path.is_file():
        solutions = json.loads(solutions_path.read_text(encoding="utf-8"))
        if task_id in solutions:
            expected_list = solutions[task_id]
            preds = fragment[task_id]
            exact = all(
                i < len(preds)
                and (
                    preds[i].get("attempt_1") == expected_list[i]
                    or preds[i].get("attempt_2") == expected_list[i]
                )
                for i in range(len(expected_list))
            )
    return {
        "ok": bool(receipt.get("ok")),
        "exact_match": exact,
        "task_id": task_id,
        "accepted_engine": receipt.get("accepted_engine"),
        "train_replay": receipt.get("train_replay"),
        "path_label": receipt.get("path_label"),
        "error": receipt.get("error"),
    }


def retest_arc3(root: Path) -> Dict[str, Any]:
    validator = root / "scripts" / "validate_arc_agi3_submission.py"
    fixture = root / "fixtures" / "kaggle_arc_format" / "submission.parquet"
    if not validator.is_file() or not fixture.is_file():
        return {"ok": False, "error": "agi3_validator_or_fixture_missing"}
    proc = subprocess.run(
        [os.environ.get("ARC_LOCAL_PARQUET_PYTHON", "python3"), str(validator), str(fixture)],
        capture_output=True,
        text=True,
        cwd=str(root),
        check=False,
    )
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": (proc.stdout or "")[:500],
        "stderr": (proc.stderr or "")[:500],
        "note": "Schema gate only; trajectory mastery remains a grammar target.",
    }


def retest_hle(root: Path, task_ids: Iterable[str]) -> Dict[str, Any]:
    """Re-run local HLE mastery script (fixtures). Never invents CAIS scores."""
    script = root / "bin" / "run-local-hle-mastery.sh"
    if not script.is_file():
        return {"ok": False, "error": "hle_mastery_script_missing"}
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = root / "reports" / f"hle_local_reinject_{run_id}"
    proc = subprocess.run(
        [str(script), "--output-dir", str(out_dir)],
        capture_output=True,
        text=True,
        cwd=str(root),
        check=False,
        env=os.environ.copy(),
    )
    receipt_path = out_dir / "receipt.json"
    matched_ids: List[str] = []
    if receipt_path.is_file():
        data = json.loads(receipt_path.read_text(encoding="utf-8"))
        wanted = set(task_ids)
        for result in data.get("results") or []:
            if result.get("id") in wanted and result.get("matched"):
                matched_ids.append(result["id"])
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "output_dir": str(out_dir.relative_to(root)) if out_dir.is_dir() else None,
        "matched_requested": matched_ids,
        "stdout_tail": (proc.stdout or "")[-800:],
        "stderr_tail": (proc.stderr or "")[-400:],
    }


def run_mastery_for_misses(
    root: Path, misses: Sequence[MissRecord], *, mode: str
) -> Dict[str, Any]:
    if mode == "none":
        return {"mode": "none", "ran": False}
    results: Dict[str, Any] = {"mode": mode, "ran": True, "tracks": {}}
    arc2_ids = [m.task_id for m in misses if m.track == TRACK_ARC2]
    arc3 = [m for m in misses if m.track == TRACK_ARC3]
    hle_ids = [m.task_id for m in misses if m.track == TRACK_HLE]

    if mode == "full":
        arc_script = root / "bin" / "run-arc-local-mastery.sh"
        if arc_script.is_file() and (arc2_ids or arc3):
            run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            report_dir = root / "reports" / f"arc_local_reinject_{run_id}"
            proc = subprocess.run(
                [str(arc_script), "--report-dir", str(report_dir)],
                capture_output=True,
                text=True,
                cwd=str(root),
                check=False,
                env=os.environ.copy(),
            )
            results["tracks"][TRACK_ARC2] = {
                "full_mastery": True,
                "returncode": proc.returncode,
                "report_dir": str(report_dir.relative_to(root)),
                "stdout_tail": (proc.stdout or "")[-800:],
            }
            results["tracks"][TRACK_ARC3] = results["tracks"][TRACK_ARC2]
        if hle_ids or mode == "full":
            results["tracks"][TRACK_HLE] = retest_hle(root, hle_ids)
        return results

    # affected (default)
    if arc2_ids:
        results["tracks"][TRACK_ARC2] = {
            "tasks": {tid: retest_arc2_task(root, tid) for tid in arc2_ids}
        }
    if arc3:
        results["tracks"][TRACK_ARC3] = retest_arc3(root)
    if hle_ids:
        # Skip soft official-gate placeholder unless real fixture misses exist.
        real = [t for t in hle_ids if t != "hle-official-gate-open"]
        if real:
            results["tracks"][TRACK_HLE] = retest_hle(root, real)
        else:
            results["tracks"][TRACK_HLE] = {
                "ok": True,
                "skipped": "official_gate_placeholder_only",
            }
    return results


def _task_state(state: LoopState, miss: MissRecord) -> Dict[str, Any]:
    key = miss.key
    if key not in state.tasks:
        state.tasks[key] = asdict(
            TaskTurnState(track=miss.track, task_id=miss.task_id, updated_at=utc_now())
        )
    return state.tasks[key]


def process_miss(
    root: Path,
    state_dir: Path,
    state: LoopState,
    miss: MissRecord,
    *,
    timeout: int,
    max_tokens: int,
    dry_run: bool,
) -> Dict[str, Any]:
    task = _task_state(state, miss)
    prior = int(task.get("turn_count") or 0)
    if prior >= state.aristotelian_closure_turns and task.get("status") != "CLOSED":
        task["status"] = "DEAD_END"
        task["last_gate"] = "ARISTOTELIAN_DEAD_END"
        task["updated_at"] = utc_now()
        append_jsonl(
            state_dir / TURNS_FILENAME,
            {
                "recorded_at_utc": utc_now(),
                "track": miss.track,
                "task_id": miss.task_id,
                "turn_index": prior,
                "turn_kind": "DEAD_END",
                "actor_role": "dispatcher",
                "gate_verdict": "ARISTOTELIAN_DEAD_END",
                "note": f"Exceeded {state.aristotelian_closure_turns} turns without C4 lock",
            },
        )
        return {
            "task_id": miss.task_id,
            "track": miss.track,
            "status": "DEAD_END",
            "turn_count": prior,
        }

    append_jsonl(
        state_dir / TURNS_FILENAME,
        {
            "recorded_at_utc": utc_now(),
            "track": miss.track,
            "task_id": miss.task_id,
            "turn_index": prior,
            "turn_kind": "OPEN",
            "actor_role": "dispatcher",
            "s_state": miss.s_state,
            "miss_source": miss.source_path,
        },
    )
    append_jsonl(
        state_dir / MISS_QUEUE_FILENAME,
        {
            "recorded_at_utc": utc_now(),
            "track": miss.track,
            "task_id": miss.task_id,
            "source_path": miss.source_path,
            "s_state": miss.s_state,
        },
    )

    if dry_run:
        repair = {
            "task_id": miss.task_id,
            "track": miss.track,
            "s1": "DRY_RUN",
            "s2": "DRY_RUN",
            "s3": "DRY_RUN",
            "s4": json.dumps(
                {
                    "typed_candidate": "DRY_RUN",
                    "validator": default_validator_for_track(miss.track),
                    "status": S4_STATUS_REINJECT,
                    "unresolved_alternatives": [],
                },
                sort_keys=True,
            ),
            "s4_status": S4_STATUS_REINJECT,
            "typed_candidate": "DRY_RUN",
            "validator": default_validator_for_track(miss.track),
            "validator_result": {"ran": False, "accepted": False, "detail": "dry_run"},
            "unresolved_alternatives": [],
            "c4_invariant": "DRY_RUN",
            "grammar_update": "dry-run placeholder — no Franklin call",
            "repair_kind": "grammar",
            "closure_ready": False,
        }
        frank = {
            "ok": True,
            "parsed": repair,
            "error": None,
            "dry_run": True,
            "endpoint": None,
            "model": None,
        }
    else:
        messages = build_franklin_messages(miss, prior)
        frank = franklin_chat(
            messages, timeout=timeout, max_tokens=max_tokens, miss=miss
        )
        repair = frank.get("parsed") or {}
        if repair:
            repair = apply_local_s4_validator(miss, repair)
        write_json(
            state_dir / RAW_RESPONSE_FILENAME,
            {
                "recorded_at_utc": utc_now(),
                "track": miss.track,
                "task_id": miss.task_id,
                "ok": bool(frank.get("ok")),
                "error": frank.get("error"),
                "endpoint": frank.get("endpoint"),
                "model": frank.get("model"),
                "fallback_used": frank.get("fallback_used"),
                "content_preview": frank.get("content_preview"),
                "parsed": repair or None,
                "protocol": "franklin_s4_projection",
            },
        )

    turn_index = prior + 1
    state.total_franklin_turns += 1
    task["turn_count"] = turn_index
    task["status"] = "HEALING"
    task["updated_at"] = utc_now()

    s4_status = str(repair.get("s4_status") or "")
    append_jsonl(
        state_dir / TURNS_FILENAME,
        {
            "recorded_at_utc": utc_now(),
            "track": miss.track,
            "task_id": miss.task_id,
            "turn_index": turn_index,
            "turn_kind": "PROPOSE",
            "actor_role": "franklin",
            "ok": bool(frank.get("ok")),
            "error": frank.get("error"),
            "endpoint": frank.get("endpoint"),
            "model": frank.get("model"),
            "elapsed_ms": frank.get("elapsed_ms"),
            "fallback_used": frank.get("fallback_used"),
            "dry_run": bool(dry_run),
            "s1": repair.get("s1"),
            "s2": repair.get("s2"),
            "s3": repair.get("s3"),
            "s4": repair.get("s4"),
            "s4_status": s4_status,
            "typed_candidate": repair.get("typed_candidate"),
            "validator": repair.get("validator"),
            "validator_result": repair.get("validator_result"),
            "c4_invariant": repair.get("c4_invariant"),
            "repair_kind": repair.get("repair_kind"),
            "protocol": "franklin_s4_projection",
            "aristotelian_turns_remaining": max(
                0, state.aristotelian_closure_turns - turn_index
            ),
        },
    )

    grammar_path = None
    live_c4 = ""
    if dry_run:
        grammar_path = record_grammar_update(state_dir, miss, repair, turn_index)
        task["last_c4"] = "DRY_RUN"
        task["last_grammar_sha"] = str(grammar_path)
        live_c4 = "DRY_RUN"
    elif repair.get("s1") or repair.get("c4_invariant") or repair.get("s4_status"):
        grammar_path = record_grammar_update(state_dir, miss, repair, turn_index)
        if s4_status == S4_STATUS_LOCKED:
            live_c4 = str(repair.get("c4_invariant") or repair.get("typed_candidate") or "")
            task["status"] = "CLOSED" if repair.get("closure_ready") else "HEALING"
        else:
            live_c4 = (
                f"REINJECT:{repair.get('c4_invariant') or repair.get('typed_candidate') or ''}"
            ).rstrip(":")
        task["last_c4"] = live_c4
        task["last_s4_status"] = s4_status
        task["last_validator"] = repair.get("validator")
        task["last_validator_result"] = repair.get("validator_result")
        task["last_grammar_sha"] = str(grammar_path)
    else:
        # Live attempt failed — clear stale DRY_RUN so health checks see real gates.
        if task.get("last_c4") == "DRY_RUN":
            task["last_c4"] = ""
        live_c4 = str(task.get("last_c4") or "")

    gate = "FRANKLIN_OK" if frank.get("ok") else f"FRANKLIN_{frank.get('error') or 'FAIL'}"
    if frank.get("fallback_used") and frank.get("ok"):
        gate = "FRANKLIN_OK_FALLBACK"
    if frank.get("ok") and s4_status == S4_STATUS_LOCKED:
        gate = "S4_LOCKED"
    elif frank.get("ok") and s4_status == S4_STATUS_REINJECT:
        gate = "S4_REINJECT"
    task["last_gate"] = gate
    append_jsonl(
        state_dir / TURNS_FILENAME,
        {
            "recorded_at_utc": utc_now(),
            "track": miss.track,
            "task_id": miss.task_id,
            "turn_index": turn_index,
            "turn_kind": "GATE",
            "actor_role": "gate",
            "gate_verdict": gate,
            "s4_status": s4_status,
            "validator_result": repair.get("validator_result"),
            "closure_ready": bool(repair.get("closure_ready")),
            "grammar_path": str(grammar_path) if grammar_path else None,
            "dry_run": bool(dry_run),
        },
    )
    return {
        "task_id": miss.task_id,
        "track": miss.track,
        "status": task["status"],
        "turn_count": turn_index,
        "gate": gate,
        "s4_status": s4_status,
        "typed_candidate": repair.get("typed_candidate"),
        "validator": repair.get("validator"),
        "validator_result": repair.get("validator_result"),
        "grammar_path": str(grammar_path) if grammar_path else None,
        "c4_invariant": live_c4 or repair.get("c4_invariant"),
        "franklin_ok": bool(frank.get("ok")),
        "error": frank.get("error"),
        "dry_run": bool(dry_run),
    }


def apply_gate_after_mastery(
    state: LoopState, miss: MissRecord, mastery: Dict[str, Any]
) -> str:
    task = _task_state(state, miss)
    track_result = (mastery.get("tracks") or {}).get(miss.track)
    closed = False
    if miss.track == TRACK_ARC2 and isinstance(track_result, dict):
        task_res = (track_result.get("tasks") or {}).get(miss.task_id) or {}
        closed = bool(task_res.get("exact_match"))
    elif miss.track == TRACK_HLE and isinstance(track_result, dict):
        closed = miss.task_id in (track_result.get("matched_requested") or [])
    elif miss.track == TRACK_ARC3 and isinstance(track_result, dict):
        # Schema green alone does not close mastery; keep HEALING.
        closed = False
    if closed:
        task["status"] = "CLOSED"
        task["last_gate"] = "LOCAL_MASTERY_CLOSED"
        task["updated_at"] = utc_now()
        return "LOCAL_MASTERY_CLOSED"
    task["status"] = "HEALING"
    task["updated_at"] = utc_now()
    return "STILL_OPEN"


def run_reinjection_cycle(
    root: Path,
    *,
    state_dir: Optional[Path] = None,
    tracks: Sequence[str] = (TRACK_ARC2, TRACK_ARC3, TRACK_HLE),
    per_track_limit: int = 4,
    mastery_mode: str = "affected",
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    dry_run: bool = False,
) -> Dict[str, Any]:
    assert_no_kaggle_submit(root)
    # Hard kill mixed writers: env EXAM_REINJECT_LIVE=1 forbids dry_run stamps.
    if dry_run and os.environ.get("EXAM_REINJECT_LIVE") == "1":
        raise RuntimeError("EXAM_REINJECT_LIVE=1 forbids --dry-run (mixed-writer cancer)")
    state_dir = state_dir or (root / "reports" / "exam_reinjection")
    state_dir.mkdir(parents=True, exist_ok=True)
    acquire_writer_lock(state_dir, dry_run=dry_run)
    try:
        state = load_state(state_dir)
        misses = load_fail_receipts(root, tracks=tracks, per_track_limit=per_track_limit)

        # Prefer non-closed, non-dead-end tasks; rotate DEAD_END after logging.
        actionable: List[MissRecord] = []
        for miss in misses:
            task = _task_state(state, miss)
            if task.get("status") == "CLOSED":
                continue
            actionable.append(miss)

        cycle_rows: List[Dict[str, Any]] = []
        for miss in actionable:
            row = process_miss(
                root,
                state_dir,
                state,
                miss,
                timeout=timeout,
                max_tokens=max_tokens,
                dry_run=dry_run,
            )
            cycle_rows.append(row)

        mastery = run_mastery_for_misses(root, actionable, mode=mastery_mode)
        for miss in actionable:
            verdict = apply_gate_after_mastery(state, miss, mastery)
            append_jsonl(
                state_dir / TURNS_FILENAME,
                {
                    "recorded_at_utc": utc_now(),
                    "track": miss.track,
                    "task_id": miss.task_id,
                    "turn_index": int((_task_state(state, miss).get("turn_count") or 0)),
                    "turn_kind": "MASTERY",
                    "actor_role": "gate",
                    "gate_verdict": verdict,
                },
            )

        state.cycles += 1
        state.last_cycle_at = utc_now()
        save_state(state_dir, state)

        # Invariant: live cycles never stamp dry_run=True.
        stamped_dry_run = bool(dry_run)
        if not stamped_dry_run and any(row.get("dry_run") for row in cycle_rows):
            raise RuntimeError("live cycle produced dry_run row — refuse stamp")

        summary = {
            "kind": "exam_miss_reinjection_cycle",
            "recorded_at_utc": state.last_cycle_at,
            "cycle": state.cycles,
            "aristotelian_closure_turns": state.aristotelian_closure_turns,
            "total_franklin_turns": state.total_franklin_turns,
            "misses_loaded": len(misses),
            "misses_actioned": len(actionable),
            "tracks": list(tracks),
            "mastery_mode": mastery_mode,
            "kaggle_submit": False,
            "no_kaggle_submit_lock": True,
            "dry_run": stamped_dry_run,
            "writer_pid": os.getpid(),
            "timeout": timeout,
            "max_tokens": max_tokens,
            "base_url": env_first(
                "EXAM_REINJECT_BASE_URL",
                "HLE_LOCAL_BASE_URL",
                "OPENAI_BASE_URL",
                default=DEFAULT_BASE_URL,
            ),
            "fallback_base_url": env_first(
                "EXAM_REINJECT_FALLBACK_BASE_URL", default=DEFAULT_FALLBACK_BASE_URL
            ),
            "rows": cycle_rows,
            "mastery": mastery,
            "open_tasks": sum(
                1 for t in state.tasks.values() if t.get("status") in {"OPEN", "HEALING"}
            ),
            "closed_tasks": sum(
                1 for t in state.tasks.values() if t.get("status") == "CLOSED"
            ),
            "dead_end_tasks": sum(
                1 for t in state.tasks.values() if t.get("status") == "DEAD_END"
            ),
            "state_dir": _rel(root, state_dir),
        }
        write_json(state_dir / CYCLE_SUMMARY_FILENAME, summary)
        write_json(
            state_dir
            / f"cycle_{state.cycles:05d}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json",
            summary,
        )
        return summary
    finally:
        # Live daemon holds the lock across cycles (EXAM_REINJECT_HOLD_LOCK=1).
        # Dry-run and one-shot live cycles release when done.
        if dry_run or os.environ.get("EXAM_REINJECT_HOLD_LOCK") != "1":
            release_writer_lock(state_dir)
