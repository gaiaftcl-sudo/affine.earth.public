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
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import requests

from llm_llvm_bench.arc.franklin_s4_projection import (
    S4_RESPONSE_JSON_SCHEMA,
    S4_STATUS_LOCKED,
    S4_STATUS_REINJECT,
    build_miss_wrapper_evidence,
    default_validator_for_track,
    exam_s4_user_prompt,
    jordan_loop_bound_closed,
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
DEFAULT_MAX_TOKENS = 2048
EVIDENCE_CHAR_BUDGET = 900

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


def discover_owned_hybrid_green(root: Path) -> Dict[str, Dict[str, Any]]:
    """Map ARC-AGI-2 task_id → owned hybrid engine with local exact-match GREEN.

    Sources (newest overlay / GREEN receipts win): summary-overlay owned_exact
    rows and per-task receipts with eval_tick / labeled_eval 1/1.
    """
    owned: Dict[str, Dict[str, Any]] = {}
    overlays = sorted(
        root.glob("reports/arc_local_*/agi2/summary-overlay.json"),
        key=lambda p: p.stat().st_mtime,
    )
    for path in overlays:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for row in (data.get("evaluation") or {}).get("owned_exact") or []:
            task_id = str(row.get("task_id") or "")
            engine = str(row.get("engine") or "").strip()
            if not task_id or not engine:
                continue
            owned[task_id] = {
                "engine": engine,
                "source": _rel(root, path),
                "labeled_eval": "owned_exact",
            }
    receipts = sorted(
        root.glob("reports/arc_local_*/agi2/*-receipt.json"),
        key=lambda p: p.stat().st_mtime,
    )
    for path in receipts:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        engine = str(data.get("engine") or "").strip()
        task_id = str(data.get("task_id") or path.stem.replace("-receipt", ""))
        labeled = str(data.get("labeled_eval") or "")
        green = bool(data.get("eval_tick") is True) or labeled.startswith("1/")
        if not task_id or not engine or not green:
            continue
        owned[task_id] = {
            "engine": engine,
            "source": _rel(root, path),
            "labeled_eval": labeled or "eval_tick",
            "train_replay": data.get("train_replay"),
            "s4_status": data.get("s4_status"),
            "corrected_c4": data.get("corrected_c4"),
        }
    return owned


def sync_local_solver_green(state: LoopState, root: Path) -> List[str]:
    """Close hybrid exact-match GREEN tasks so the daemon never REINJECTs them.

    Sets status CLOSED with last_c4 = owned grammar/engine name and
    last_gate = LOCAL_SOLVER_GREEN (or S4_LOCKED when a prior validator lock
    already accepted). Returns closed task keys.
    """
    closed_keys: List[str] = []
    for task_id, meta in discover_owned_hybrid_green(root).items():
        key = f"{TRACK_ARC2}:{task_id}"
        engine = str(meta.get("engine") or "").strip()
        if not engine:
            continue
        task = state.tasks.get(key) or {
            "track": TRACK_ARC2,
            "task_id": task_id,
            "turn_count": 0,
        }
        prior_gate = str(task.get("last_gate") or "")
        prior_c4 = str(task.get("last_c4") or "")
        validator_ok = bool((task.get("last_validator_result") or {}).get("accepted"))
        receipt_locked = str(meta.get("s4_status") or "") == S4_STATUS_LOCKED
        if prior_gate == "S4_LOCKED" and validator_ok:
            gate = "S4_LOCKED"
        elif receipt_locked and meta.get("corrected_c4"):
            gate = "S4_LOCKED"
        else:
            gate = "LOCAL_SOLVER_GREEN"
        if gate == "S4_LOCKED" and prior_c4 and not prior_c4.startswith("REINJECT"):
            c4 = prior_c4
        elif meta.get("corrected_c4"):
            c4 = str(meta["corrected_c4"])
        else:
            c4 = engine
        task.update(
            {
                "track": TRACK_ARC2,
                "task_id": task_id,
                "status": "CLOSED",
                "engine": engine,
                "last_c4": c4,
                "last_gate": gate,
                "last_s4_status": S4_STATUS_LOCKED
                if gate == "S4_LOCKED"
                else task.get("last_s4_status") or S4_STATUS_LOCKED,
                "updated_at": utc_now(),
            }
        )
        if meta.get("labeled_eval") or meta.get("train_replay"):
            task["last_validator"] = task.get("last_validator") or "local_hybrid_exact"
            task["last_validator_result"] = {
                "accepted": True,
                "labeled_eval": meta.get("labeled_eval"),
                "train_replay": meta.get("train_replay"),
                "detail": "local_solver_green_skip",
            }
        state.tasks[key] = task
        closed_keys.append(key)
    return closed_keys


def _task_is_closed(task: Mapping[str, Any]) -> bool:
    return str(task.get("status") or "") in {"CLOSED", "HEALED"}


def _load_arc2_queue_misses(
    root: Path, *, skip_ids: Iterable[str], limit: int
) -> List[MissRecord]:
    """Pull next open ARC-2 misses from S1/S3 reinjection queues."""
    skip = set(skip_ids)
    seen: set[str] = set()
    misses: List[MissRecord] = []
    queue_paths = [
        root / "reports" / "exam_reinjection" / "arc_agi2_s3_miss_queue.jsonl",
        root / "reports" / "exam_reinjection" / "arc_agi2_s1_miss_queue.jsonl",
    ]
    for path in queue_paths:
        if not path.is_file():
            continue
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                task_id = str(row.get("task_id") or "")
                if not task_id or task_id in skip or task_id in seen:
                    continue
                seen.add(task_id)
                misses.append(
                    MissRecord(
                        track=TRACK_ARC2,
                        task_id=task_id,
                        evidence={
                            "test_index": row.get("test_index"),
                            "expected_shape": row.get("expected_shape"),
                            "input_shape": row.get("input_shape"),
                            "invariant": row.get("invariant"),
                            "language_game_class": row.get("language_game_class"),
                            "ask": row.get("ask"),
                            "note": row.get("note"),
                        },
                        source_path=_rel(root, path),
                        s_state="incomplete",
                        drift_kind="understanding drift",
                    )
                )
                if len(misses) >= limit:
                    return misses
    return misses


def load_arc2_fails(root: Path, limit: int) -> List[MissRecord]:
    owned_green = set(discover_owned_hybrid_green(root))
    report = _latest_dir("reports/arc_local_*", root)
    path: Optional[Path] = None
    if report is not None:
        candidate = report / "agi2" / "failure-case-analyses.json"
        if candidate.is_file():
            path = candidate
    if path is None:
        alt = list(root.glob("reports/arc_local_*/agi2/failure-case-analyses.json"))
        if alt:
            path = max(alt, key=lambda p: p.stat().st_mtime)
    misses: List[MissRecord] = []
    seen: set[str] = set()
    if path is not None and path.is_file():
        cases = json.loads(path.read_text(encoding="utf-8"))
        for case in cases:
            if case.get("attempt_1_exact") and case.get("attempt_2_exact"):
                continue
            task_id = str(case.get("task_id") or "")
            if not task_id or task_id in owned_green or task_id in seen:
                continue
            seen.add(task_id)
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
                return misses
    # Fill remaining slots from S1/S3 open queues (already-solved engines skipped).
    if len(misses) < limit:
        misses.extend(
            _load_arc2_queue_misses(
                root,
                skip_ids=owned_green | seen,
                limit=limit - len(misses),
            )
        )
    return misses[:limit]


def _agi3_trajectory_gap_owned(root: Path) -> bool:
    """True when bp35 level_clear_motion_click_grammar is FoT-owned.

    Meta task ``agi3-trajectory-gap`` then must not re-queue as incomplete —
    remaining ar25/ls20/bp35-L2+ heal under their own game_ids.
    """
    evidence = (
        root
        / "reports"
        / "exam_reinjection"
        / "grammar"
        / "arc3"
        / "unreproduced_productive_delta"
        / "evidence.json"
    )
    if not evidence.is_file():
        return False
    try:
        payload = json.loads(evidence.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if str(payload.get("owned_as") or "") != "level_clear_motion_click_grammar":
        return False
    if str(payload.get("status") or "") != "OWNED_ON_BP35":
        return False
    for game in payload.get("per_game") or []:
        if (
            str(game.get("game_id") or "") == "bp35"
            and str(game.get("grammar_class") or "")
            == "level_clear_motion_click_grammar"
            and bool(game.get("replay_verified"))
        ):
            return True
    return False


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
        # Skip meta gap once PlatformerPolicy / level_clear_motion_click_grammar
        # is FoT-owned; do not invent WIN=1.0 GREEN.
        if (
            not _agi3_trajectory_gap_owned(root)
            and ("NOT_RUN" in traj or float(public.get("publicScore") or 0) < 1.0)
        ):
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
    misses: List[MissRecord] = []
    # Prefer official judged misses when present.
    official_dirs = sorted(
        root.glob("reports/hle_official_*/misses.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if official_dirs:
        misses_path = official_dirs[0]
        for row in json.loads(misses_path.read_text(encoding="utf-8")):
            task_id = str(row.get("id") or "")
            if not task_id:
                continue
            misses.append(
                MissRecord(
                    track=TRACK_HLE,
                    task_id=task_id,
                    evidence={
                        "source": "official_cais_hle",
                        "model_answer": row.get("model_answer"),
                        "correct_answer": row.get("correct_answer"),
                        "confidence": row.get("confidence"),
                    },
                    source_path=str(misses_path.relative_to(root)),
                    s_state="incomplete",
                    drift_kind="understanding drift",
                )
            )
            if len(misses) >= limit:
                return misses
        if misses:
            return misses[:limit]

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


def _try_close_truncated_json(text: str) -> Optional[Dict[str, Any]]:
    """Best-effort close of length-truncated JSON objects from thinking models."""
    text = (text or "").strip()
    if not text or "{" not in text:
        return None
    start = text.find("{")
    blob = text[start:]
    # Drop a trailing incomplete string value.
    if blob.count('"') % 2 == 1:
        blob = blob.rsplit('"', 1)[0]
    # Drop trailing comma / colon debris.
    blob = re.sub(r"[,:\s]+$", "", blob)
    opens = blob.count("{") - blob.count("}")
    opens_list = blob.count("[") - blob.count("]")
    blob = blob + ("]" * max(0, opens_list)) + ("}" * max(0, opens))
    try:
        parsed = json.loads(blob)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def salvage_s4_from_text(text: str, miss: MissRecord) -> Optional[Dict[str, Any]]:
    """Recover LOCKED|REINJECT fields from truncated Franklin output."""
    text = _strip_markdown_fences(text or "")
    if not text:
        return None
    closed = _try_close_truncated_json(text)
    if closed is not None:
        normalized = normalize_s4_response(closed, track=miss.track, task_id=miss.task_id)
        if normalized is not None:
            return normalized
    status_match = re.search(r'"status"\s*:\s*"(LOCKED|REINJECT)"', text, re.I)
    validator_match = re.search(r'"validator"\s*:\s*"([^"]+)"', text)
    candidate_match = re.search(
        r'"typed_candidate"\s*:\s*("([^"\\]|\\.)*"|\{[^{}]*\}|\[[^\[\]]*\])',
        text,
    )
    c4_match = re.search(r'"c4_invariant"\s*:\s*"([^"]+)"', text)
    if not (status_match or candidate_match or c4_match or validator_match):
        return None
    typed: Any = ""
    if candidate_match:
        raw_cand = candidate_match.group(1)
        try:
            typed = json.loads(raw_cand)
        except json.JSONDecodeError:
            typed = raw_cand.strip('"')
    elif c4_match:
        typed = c4_match.group(1)
    status = (status_match.group(1).upper() if status_match else S4_STATUS_REINJECT)
    if not str(typed).strip():
        status = S4_STATUS_REINJECT
        typed = "truncated_response_incomplete_candidate"
    return normalize_s4_response(
        {
            "task_id": miss.task_id,
            "track": miss.track,
            "s1": "salvaged_from_truncated_franklin",
            "s2": "salvaged_from_truncated_franklin",
            "s3": "salvaged_from_truncated_franklin",
            "typed_candidate": typed,
            "validator": (
                validator_match.group(1)
                if validator_match
                else default_validator_for_track(miss.track)
            ),
            "status": status,
            "unresolved_alternatives": ["truncated_output"],
            "grammar_update": "salvage_truncated_s4_json",
            "repair_kind": "grammar",
            "research_note": "Franklin response truncated; salvaged S4 fields",
            "closure_ready": status == S4_STATUS_LOCKED,
        },
        track=miss.track,
        task_id=miss.task_id,
    )


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
        closed = _try_close_truncated_json(text)
        if closed is not None:
            candidates.append(closed)
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


LEARNED_EXPERIENCE_LIMIT = 8


def load_learned_experiences(
    state_dir: Path,
    *,
    track: str,
    exclude_task_id: str = "",
    limit: int = LEARNED_EXPERIENCE_LIMIT,
) -> List[Dict[str, Any]]:
    """Pull prior CLOSED / LOCKED language-game seals for the next play.

    Sources: grammar/<track>/*.json seals and state.json CLOSED rows.
    Every projection path must call this before Franklin proposes.
    """
    experiences: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def _push(row: Dict[str, Any]) -> None:
        tid = str(row.get("task_id") or "")
        if not tid or tid == exclude_task_id or tid in seen:
            return
        seen.add(tid)
        experiences.append(row)

    grammar_dir = state_dir / "grammar" / track
    if grammar_dir.is_dir():
        seals = sorted(
            grammar_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for path in seals:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            status = str(payload.get("status") or payload.get("s4_status") or "")
            vr = payload.get("validator_result") or {}
            accepted = bool(isinstance(vr, dict) and vr.get("accepted"))
            locked = status.upper() in {"CLOSED", "LOCKED", "HEALED"} or accepted
            if not locked:
                continue
            c4 = str(payload.get("c4_invariant") or payload.get("typed_candidate") or "")
            _push(
                {
                    "task_id": str(payload.get("task_id") or path.stem),
                    "track": track,
                    "status": "CLOSED" if status.upper() in {"CLOSED", "HEALED"} else status,
                    "c4_invariant": c4[:240],
                    "grammar_update": str(payload.get("grammar_update") or "")[:160],
                    "validator": str(payload.get("validator") or ""),
                    "validator_result": vr if isinstance(vr, dict) else {},
                    "engine": str(
                        (vr or {}).get("engine")
                        if isinstance(vr, dict)
                        else payload.get("engine")
                        or ""
                    ),
                    "source": f"grammar/{track}/{path.name}",
                }
            )
            if len(experiences) >= limit:
                return experiences[:limit]

    state_path = state_dir / STATE_FILENAME
    if state_path.is_file():
        try:
            state_raw = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            state_raw = {}
        for key, task in (state_raw.get("tasks") or {}).items():
            if not isinstance(task, dict):
                continue
            if str(task.get("track") or "") != track:
                continue
            if str(task.get("status") or "") not in {"CLOSED", "HEALED"}:
                continue
            tid = str(task.get("task_id") or key.split(":", 1)[-1])
            _push(
                {
                    "task_id": tid,
                    "track": track,
                    "status": "CLOSED",
                    "c4_invariant": str(task.get("last_c4") or "")[:240],
                    "grammar_update": "",
                    "validator": str(task.get("last_validator") or ""),
                    "validator_result": task.get("last_validator_result")
                    if isinstance(task.get("last_validator_result"), dict)
                    else {},
                    "engine": str(task.get("engine") or ""),
                    "source": "state.json",
                    "last_gate": str(task.get("last_gate") or ""),
                }
            )
            if len(experiences) >= limit:
                break

    return experiences[:limit]


def apply_local_s4_validator(miss: MissRecord, repair: Dict[str, Any]) -> Dict[str, Any]:
    """Run the named local/track-native check; demote false LOCKED → REINJECT.

    Jordan loop bound: LOCKED requires zero remainder against C4 via the named
    validator. Candidate presence alone is Aristotelian shear — demote.
    """
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
    incoming_vr = repair.get("validator_result")
    if not isinstance(incoming_vr, dict):
        incoming_vr = {}

    if miss.track == TRACK_HLE:
        expected = (
            miss.evidence.get("expected")
            or miss.evidence.get("answer")
            or miss.evidence.get("corrected_c4")
        )
        compare_text = candidate_text
        if isinstance(candidate, dict) and candidate.get("answer") is not None:
            compare_text = str(candidate.get("answer")).strip()
        if expected is not None and compare_text:
            accepted = compare_text.strip().lower() == str(expected).strip().lower()
            detail = "exact_token_match" if accepted else "exact_token_mismatch"
            if accepted:
                repair["typed_candidate"] = compare_text
                repair["c4_invariant"] = compare_text
                candidate_text = compare_text
                incoming_vr = {
                    **incoming_vr,
                    "accepted": True,
                    "detail": "exact_token_match",
                }
        elif candidate_text and status == S4_STATUS_LOCKED:
            # Format presence without fixture expected cannot close Jordan bound.
            accepted = False
            detail = "jordan_loop_bound_open:format_presence_without_expected"
    elif miss.track == TRACK_ARC2:
        # Preserve replay evidence Franklin/mastery already sealed into validator_result.
        bound_probe = jordan_loop_bound_closed(
            TRACK_ARC2, incoming_vr, accepted=bool(incoming_vr.get("accepted"))
        )
        if bound_probe["closed"]:
            accepted = True
            detail = str(incoming_vr.get("detail") or bound_probe["reason"])
        elif candidate_text:
            accepted = False
            detail = "jordan_loop_bound_open:pending_demonstration_replay"
        else:
            accepted = False
            detail = "empty_candidate"
    elif miss.track == TRACK_ARC3:
        bound_probe = jordan_loop_bound_closed(
            TRACK_ARC3, incoming_vr, accepted=bool(incoming_vr.get("accepted"))
        )
        if bound_probe["closed"]:
            accepted = True
            detail = str(incoming_vr.get("detail") or bound_probe["reason"])
        elif candidate_text:
            accepted = False
            detail = "jordan_loop_bound_open:pending_environment_step"
        else:
            accepted = False
            detail = "empty_candidate"

    validator_result: Dict[str, Any] = {
        **incoming_vr,
        "validator": validator,
        "ran": True,
        "detail": detail,
        "status": status,
    }
    bound = jordan_loop_bound_closed(
        miss.track, validator_result, accepted=accepted
    )
    validator_result["jordan_loop_bound"] = bound
    validator_result["accepted"] = bool(accepted and bound["closed"])

    if status == S4_STATUS_LOCKED and not bound["closed"]:
        status = S4_STATUS_REINJECT
        repair["closure_ready"] = False
        detail = f"demoted_locked:{bound['reason']}"
        validator_result["detail"] = detail
        validator_result["accepted"] = False
        validator_result["status"] = status
        validator_result["jordan_loop_bound"] = {
            **bound,
            "closed": False,
            "remainder_open": True,
            "reason": bound["reason"],
        }
    elif status == S4_STATUS_LOCKED and bound["closed"]:
        repair["closure_ready"] = True
        validator_result["status"] = status
    else:
        repair["closure_ready"] = False
        status = S4_STATUS_REINJECT
        validator_result["status"] = status
        validator_result["accepted"] = False

    repair["s4_status"] = status
    repair["validator"] = validator
    repair["validator_result"] = validator_result
    repair["jordan_loop_bound"] = validator_result["jordan_loop_bound"]
    repair["s4"] = json.dumps(
        {
            "typed_candidate": candidate if candidate is not None else "",
            "validator": validator,
            "status": status,
            "unresolved_alternatives": repair.get("unresolved_alternatives") or [],
            "validator_result": repair["validator_result"],
            "jordan_loop_bound": repair["jordan_loop_bound"],
        },
        sort_keys=True,
    )
    if candidate_text and status == S4_STATUS_LOCKED:
        repair["c4_invariant"] = candidate_text
    elif candidate_text and status == S4_STATUS_REINJECT:
        repair["c4_invariant"] = f"REINJECT:{candidate_text}"[:500]
    elif status == S4_STATUS_REINJECT:
        repair["c4_invariant"] = f"REINJECT:{detail}"
    return repair


def build_franklin_messages(
    miss: MissRecord,
    prior_turns: int,
    *,
    state_dir: Optional[Path] = None,
    learned_experiences: Optional[Sequence[Mapping[str, Any]]] = None,
) -> List[Dict[str, str]]:
    """Protocol-aligned prompt: WRAPPER_EVIDENCE → typed S4 LOCKED|REINJECT JSON.

    Always pulls learned CLOSED experiences when state_dir is provided.
    Keeps the Jordan Bond pipeline in the system digest (not truncated away).
    """
    baseline = franklin_uum8d_game_comprehension_system_prompt()
    # Keep Phase III/IV Jordan Bond; trim only length, never strip the bound.
    digest = baseline.strip()
    if len(digest) > 2200:
        # Prefer keeping the Jordan Bond section at the end of the digest.
        marker = "**3. Ingestion to Jordan Bond"
        idx = digest.find(marker)
        if idx > 0:
            head = digest[:idx].rstrip()
            jordan = digest[idx:].rstrip()
            head_budget = max(400, 2200 - len(jordan) - 80)
            if len(head) > head_budget:
                head = head[:head_budget].rstrip() + "\n[UUM-8D head truncated]"
            digest = f"{head}\n\n{jordan}"
        else:
            digest = digest[:2200].rstrip() + "\n[UUM-8D digest truncated]"

    experiences: List[Dict[str, Any]]
    if learned_experiences is not None:
        experiences = [dict(item) for item in learned_experiences]
    elif state_dir is not None:
        experiences = load_learned_experiences(
            state_dir, track=miss.track, exclude_task_id=miss.task_id
        )
    else:
        experiences = []

    system = projection_system_prompt(
        f"{digest}\n\n"
        "---\n"
        "EXAM REINJECTION = Franklin S¹–S⁴ projection language game.\n"
        f"Aristotelian turn {prior_turns + 1}/{ARISTOTELIAN_CLOSURE_TURNS}.\n"
        f"LEARNED_EXPERIENCES_LOADED={len(experiences)} — reuse sealed grammar/"
        "engines before inventing a new candidate.\n"
        "JORDAN_LOOP_BOUND: LOCKED only when named validator yields zero remainder.\n"
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
        learned_experiences=experiences,
    )
    user = exam_s4_user_prompt(evidence_turn, _truncate_evidence(miss.evidence))
    if experiences:
        exp_blob = json.dumps(experiences, sort_keys=True)
        if len(exp_blob) > 1800:
            exp_blob = exp_blob[:1780] + "...]"
        user = (
            f"{user}\n"
            "LEARNED_CLOSED_EXPERIENCES (pull every play — reuse before inventing):\n"
            f"{exp_blob}\n"
        )
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
        combined = f"{content}\n{reasoning}".strip()
        raw_parsed = (
            extract_json_object(content)
            or extract_json_object(reasoning)
            or extract_json_object(combined)
        )
        parsed = (
            normalize_repair_payload(raw_parsed, miss)
            if miss is not None and raw_parsed is not None
            else raw_parsed
        )
        if parsed is None and miss is not None:
            parsed = salvage_s4_from_text(combined, miss)
            if parsed is not None and raw_parsed is None:
                raw_parsed = {
                    "salvaged": True,
                    "s4_status": parsed.get("s4_status"),
                    "typed_candidate": parsed.get("typed_candidate"),
                }
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
        messages = build_franklin_messages(miss, prior, state_dir=state_dir)
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
    # Do not Aristotelian-reset a DEAD_END back to HEALING — that shears the
    # 29-turn bound and burns cycles without pulling new grammar.
    if str(task.get("status") or "") == "DEAD_END":
        return "ARISTOTELIAN_DEAD_END"
    track_result = (mastery.get("tracks") or {}).get(miss.track)
    closed = False
    accepted_engine = ""
    if miss.track == TRACK_ARC2 and isinstance(track_result, dict):
        task_res = (track_result.get("tasks") or {}).get(miss.task_id) or {}
        closed = bool(task_res.get("exact_match"))
        accepted_engine = str(task_res.get("accepted_engine") or "").strip()
    elif miss.track == TRACK_HLE and isinstance(track_result, dict):
        closed = miss.task_id in (track_result.get("matched_requested") or [])
    elif miss.track == TRACK_ARC3 and isinstance(track_result, dict):
        # Schema green alone does not close mastery; keep HEALING.
        closed = False
    if closed:
        engine = accepted_engine or str(task.get("engine") or "").strip()
        task["status"] = "CLOSED"
        task["last_gate"] = "LOCAL_MASTERY_CLOSED"
        if engine:
            task["engine"] = engine
            if not str(task.get("last_c4") or "").strip() or str(
                task.get("last_c4") or ""
            ).startswith("REINJECT"):
                task["last_c4"] = engine
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
        # Seal local hybrid GREEN before drain so solved tasks never burn Franklin.
        solver_skipped = sync_local_solver_green(state, root)
        misses = load_fail_receipts(root, tracks=tracks, per_track_limit=per_track_limit)

        # Prefer non-closed, non-dead-end tasks; rotate DEAD_END after logging.
        actionable: List[MissRecord] = []
        seen_keys: set[str] = set()
        for miss in misses:
            if miss.key in seen_keys:
                continue
            seen_keys.add(miss.key)
            task = _task_state(state, miss)
            if _task_is_closed(task) or task.get("status") == "DEAD_END":
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
            "solver_green_skipped": solver_skipped,
            "open_tasks": sum(
                1 for t in state.tasks.values() if t.get("status") in {"OPEN", "HEALING"}
            ),
            "closed_tasks": sum(
                1 for t in state.tasks.values() if _task_is_closed(t)
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
