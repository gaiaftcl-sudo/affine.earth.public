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

from llm_llvm_bench.arc.franklin_uum8d_system_prompt import (
    franklin_uum8d_game_comprehension_system_prompt,
)

ARISTOTELIAN_CLOSURE_TURNS = 29
STATE_FILENAME = "state.json"
TURNS_FILENAME = "turns.jsonl"
GRAMMAR_FILENAME = "grammar_updates.jsonl"
MISS_QUEUE_FILENAME = "miss_queue.jsonl"
CYCLE_SUMMARY_FILENAME = "latest_cycle.json"

TRACK_ARC2 = "arc2"
TRACK_ARC3 = "arc3"
TRACK_HLE = "hle"


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


def extract_json_object(text: str) -> Optional[Dict[str, Any]]:
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


def build_franklin_messages(miss: MissRecord, prior_turns: int) -> List[Dict[str, str]]:
    baseline = franklin_uum8d_game_comprehension_system_prompt()
    system = (
        f"{baseline}\n\n"
        "---\n"
        "You are in a two-way language game with the local exam wrapper.\n"
        "A prior attempt MISSED. That means the S-state (S1–S4) is incomplete — "
        "not that compute failed.\n"
        "Repair the game grammar so C1–C4 collapses to a SINGLE C4 projection "
        "(the only true answer).\n"
        f"Aristotelian closure budget: turn {prior_turns + 1} of "
        f"{ARISTOTELIAN_CLOSURE_TURNS}.\n"
        "Return exactly one JSON object with keys:\n"
        "task_id, track, s1, s2, s3, s4, c4_invariant, grammar_update, "
        "repair_kind, research_note, closure_ready.\n"
        "repair_kind ∈ {grammar, solver_hint, context, action_theory}.\n"
        "Do not guess grids or answers without locking C4. No Kaggle submit."
    )
    user = (
        f"track: {miss.track}\n"
        f"task_id: {miss.task_id}\n"
        f"s_state: {miss.s_state}\n"
        f"drift_kind: {miss.drift_kind}\n"
        f"source: {miss.source_path}\n"
        f"miss_evidence:\n{json.dumps(miss.evidence, indent=2, sort_keys=True)}\n"
        "Set S1 (objects/symbols), S2 (relations), S3 (legal transforms/actions), "
        "S4 (acceptance boundary). Then lock C4."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def franklin_chat(
    messages: List[Dict[str, str]],
    *,
    timeout: int,
    max_tokens: int,
) -> Dict[str, Any]:
    base_url = env_first(
        "EXAM_REINJECT_BASE_URL",
        "HLE_LOCAL_BASE_URL",
        "OPENAI_BASE_URL",
        "AFFINE_HARNESS_ENDPOINT",
        default="http://127.0.0.1:8080/v1",
    )
    api_key = env_first(
        "OPENAI_API_KEY", "AFFINE_HARNESS_API_KEY", default="uum8d-exam-reinject"
    )
    model = env_first(
        "EXAM_REINJECT_MODEL", "HLE_LOCAL_MODEL", "OPENAI_MODEL", "AFFINE_HARNESS_MODEL"
    )
    assert base_url is not None and api_key is not None
    session = requests.Session()
    if not model:
        models_response = session.get(
            f"{base_url.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            timeout=min(timeout, 15),
        )
        if models_response.ok:
            model_ids = [
                item.get("id") for item in models_response.json().get("data", [])
            ]
            model = next(
                (item for item in model_ids if item and "embed" not in item), None
            )
    if not model:
        return {
            "ok": False,
            "error": "NO_CHAT_MODEL",
            "content": "",
            "parsed": None,
            "endpoint": base_url.rstrip("/"),
            "model": None,
        }
    started = time.perf_counter()
    try:
        response = session.post(
            f"{base_url.rstrip('/')}/chat/completions",
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
        return {
            "ok": False,
            "error": f"TRANSPORT:{exc}",
            "content": "",
            "parsed": None,
            "endpoint": base_url.rstrip("/"),
            "model": model,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        }
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    if not response.ok:
        return {
            "ok": False,
            "error": f"HTTP_{response.status_code}",
            "content": response.text[:2000],
            "parsed": None,
            "endpoint": base_url.rstrip("/"),
            "model": model,
            "elapsed_ms": elapsed_ms,
        }
    payload = response.json()
    message = payload["choices"][0]["message"]
    content = str(message.get("content") or "")
    reasoning = str(message.get("reasoning_content") or "")
    parsed = extract_json_object(content) or extract_json_object(reasoning)
    return {
        "ok": parsed is not None,
        "error": None if parsed is not None else "PARSE_FAIL",
        "content": content or reasoning,
        "parsed": parsed,
        "endpoint": base_url.rstrip("/"),
        "model": model,
        "elapsed_ms": elapsed_ms,
        "usage": payload.get("usage", {}),
    }


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
        "c4_invariant": repair.get("c4_invariant"),
        "grammar_update": repair.get("grammar_update"),
        "repair_kind": repair.get("repair_kind"),
        "research_note": repair.get("research_note"),
        "closure_ready": bool(repair.get("closure_ready")),
        "source_miss": miss.source_path,
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
            "s4": "DRY_RUN",
            "c4_invariant": "DRY_RUN",
            "grammar_update": "dry-run placeholder — no Franklin call",
            "repair_kind": "grammar",
            "closure_ready": False,
        }
        frank = {"ok": True, "parsed": repair, "error": None, "dry_run": True}
    else:
        messages = build_franklin_messages(miss, prior)
        frank = franklin_chat(messages, timeout=timeout, max_tokens=max_tokens)
        repair = frank.get("parsed") or {}

    turn_index = prior + 1
    state.total_franklin_turns += 1
    task["turn_count"] = turn_index
    task["status"] = "HEALING"
    task["updated_at"] = utc_now()

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
            "s1": repair.get("s1"),
            "s2": repair.get("s2"),
            "s3": repair.get("s3"),
            "s4": repair.get("s4"),
            "c4_invariant": repair.get("c4_invariant"),
            "repair_kind": repair.get("repair_kind"),
            "aristotelian_turns_remaining": max(
                0, state.aristotelian_closure_turns - turn_index
            ),
        },
    )

    grammar_path = None
    if repair.get("s1") or repair.get("c4_invariant") or repair.get("grammar_update"):
        grammar_path = record_grammar_update(state_dir, miss, repair, turn_index)
        task["last_c4"] = str(repair.get("c4_invariant") or "")
        task["last_grammar_sha"] = str(grammar_path)

    gate = "FRANKLIN_OK" if frank.get("ok") else f"FRANKLIN_{frank.get('error') or 'FAIL'}"
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
            "closure_ready": bool(repair.get("closure_ready")),
            "grammar_path": str(grammar_path) if grammar_path else None,
        },
    )
    return {
        "task_id": miss.task_id,
        "track": miss.track,
        "status": task["status"],
        "turn_count": turn_index,
        "gate": gate,
        "grammar_path": str(grammar_path) if grammar_path else None,
        "c4_invariant": repair.get("c4_invariant"),
        "franklin_ok": bool(frank.get("ok")),
        "error": frank.get("error"),
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
    timeout: int = 180,
    max_tokens: int = 2048,
    dry_run: bool = False,
) -> Dict[str, Any]:
    assert_no_kaggle_submit(root)
    state_dir = state_dir or (root / "reports" / "exam_reinjection")
    state_dir.mkdir(parents=True, exist_ok=True)
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
        "dry_run": dry_run,
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
        state_dir / f"cycle_{state.cycles:05d}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json",
        summary,
    )
    return summary
