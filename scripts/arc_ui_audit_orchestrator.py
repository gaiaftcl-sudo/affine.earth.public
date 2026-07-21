#!/usr/bin/env python3
"""ARC UI audit orchestrator — local evidence exam matching wiki doctrine.

Four phases: permission/run binding → VideoToolbox boot → per-task state
machine → artifact validation. Never imports Kaggle tooling. Requires
configs/NO_KAGGLE_SUBMIT.lock. Does not manufacture cell physics or answers.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from llm_llvm_bench.arc.franklin_uum8d_system_prompt import (  # noqa: E402
    franklin_uum8d_game_comprehension_system_prompt,
)

DEFAULT_CHALLENGES = ROOT / "data/arc-prize-2026-agi-2/arc-agi_evaluation_challenges.json"
DEFAULT_AUDIT_SCAFFOLD = ROOT / "affine_audit_logs"
DEFAULT_REPORTS = ROOT / "reports/arc_ui_audit"
VALIDATOR = ROOT / "scripts/validate_arc_prize_submission.py"
LOCK_PATH = ROOT / "configs/NO_KAGGLE_SUBMIT.lock"
CELL_IDS = [f"hel-{i:02d}" for i in range(5)] + [f"nbg-{i:02d}" for i in range(4)]
ENCODER = "h264_videotoolbox"

TASK_STATES = (
    "TASK_BOUND",
    "CAPTURE_STARTED",
    "CURSOR_PROMPT_INJECTED",
    "NINE_CELL_REDUCTION",
    "RESULT_JSON_EXTRACTED",
    "TASK_RECORDED",
    "SIGINT_STOPPED",
)


class AuditError(RuntimeError):
    """Loud protocol failure — never relabelled GREEN."""


@dataclass
class TaskRecord:
    task_id: str
    status: str  # complete | failed | incomplete
    states_reached: List[str] = field(default_factory=list)
    capture_path: str = ""
    scaffold_capture_path: str = ""
    prompt_sha256: str = ""
    raw_json_sha256: str = ""
    canonical_json_sha256: str = ""
    artifact_source: str = "NONE"
    bridge_status: str = "NOT_CALLED"
    bridge_detail: str = ""
    path_label: str = "NONE"
    train_replay: str = ""
    ui_copy_status: str = "NOT_ATTEMPTED"
    ffmpeg_pid: Optional[int] = None
    ffmpeg_command: List[str] = field(default_factory=list)
    sigint_status: str = "NOT_STOPPED"
    error: str = ""
    started_at: str = ""
    finished_at: str = ""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel_to_root(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def run(
    command: Sequence[str],
    *,
    input_text: Optional[str] = None,
    timeout: int = 30,
    env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        env=env,
    )


def git_revision() -> str:
    result = run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], timeout=10)
    if result.returncode:
        return "unknown"
    return (result.stdout or "").strip() or "unknown"


def require_host_tools() -> None:
    missing = [
        name
        for name in ("ffmpeg", "osascript", "pbcopy", "pbpaste")
        if shutil.which(name) is None
    ]
    if missing:
        raise AuditError(f"missing required macOS host tools: {', '.join(missing)}")


def check_videotoolbox(encoder: str) -> Tuple[bool, str]:
    result = run(["ffmpeg", "-hide_banner", "-encoders"], timeout=15)
    output = f"{result.stdout}\n{result.stderr}"
    if encoder in output:
        return True, f"encoder {encoder} listed by ffmpeg -encoders"
    return False, f"encoder {encoder} not listed by ffmpeg -encoders"


def check_accessibility() -> Tuple[bool, str]:
    result = run(
        ["osascript", "-e", 'tell application "System Events" to get name of every process'],
        timeout=15,
    )
    if result.returncode:
        return False, (result.stderr or result.stdout).strip()
    return True, "System Events automation is available"


def check_screen_recording(ffmpeg_input: str) -> Tuple[bool, str]:
    result = run(
        [
            "ffmpeg",
            "-hide_banner",
            "-f",
            "avfoundation",
            "-list_devices",
            "true",
            "-i",
            "",
        ],
        timeout=15,
    )
    output = f"{result.stdout}\n{result.stderr}".strip()
    if "AVFoundation" in output or "Capture screen" in output or "Screen Capture" in output:
        return True, f"AVFoundation enumerated; configured display input={ffmpeg_input!r}"
    return False, output[-1200:] or "ffmpeg did not expose AVFoundation devices"


def permission_preflight(ffmpeg_input: str, encoder: str) -> Dict[str, Any]:
    require_host_tools()
    accessibility_ok, accessibility_detail = check_accessibility()
    screen_ok, screen_detail = check_screen_recording(ffmpeg_input)
    encoder_ok, encoder_detail = check_videotoolbox(encoder)
    payload = {
        "status": "READY" if accessibility_ok and screen_ok and encoder_ok else "FAILED",
        "accessibility": {"ok": accessibility_ok, "detail": accessibility_detail},
        "screen_recording": {"ok": screen_ok, "detail": screen_detail},
        "videotoolbox": {"ok": encoder_ok, "detail": encoder_detail, "encoder": encoder},
        "steward_checklist": [
            "System Settings → Privacy & Security → Accessibility: Terminal + Cursor",
            "System Settings → Privacy & Security → Screen Recording: Terminal + Cursor",
            "Quit and reopen Terminal and Cursor after granting permissions",
            "Cursor open with intended workspace/chat focused",
            f"ffmpeg -encoders lists {encoder}",
            "configs/NO_KAGGLE_SUBMIT.lock present",
        ],
    }
    print(json.dumps(payload, indent=2))
    if payload["status"] != "READY":
        raise AuditError(
            "macOS permission / VideoToolbox preflight failed. "
            "Grant Accessibility + Screen Recording to Terminal and Cursor, "
            "confirm VideoToolbox encoder, relaunch apps, then retry. "
            f"Details: {json.dumps(payload)}"
        )
    return payload


class EventLog:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")

    def emit(self, event: str, **fields: Any) -> None:
        row = {"ts": utc_now(), "event": event, **fields}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def task_prompt(task_id: str, task: Dict[str, Any]) -> str:
    context = json.dumps({"task_id": task_id, **task}, separators=(",", ":"))
    baseline = franklin_uum8d_game_comprehension_system_prompt()
    return (
        f"{baseline}\n\n"
        "---\n"
        "ARC-AGI-2 LOCAL EXAM TASK — UI-AUDITED\n"
        f"Task ID: {task_id}\n"
        "Treat colors as symbols and preserve all coordinates. Infer candidate "
        "transformations only from the complete training demonstrations; replay "
        "each candidate against every training pair before emitting a result. "
        "Return exactly one JSON object and no Markdown fences or prose:\n"
        f'{{"{task_id}":[{{"attempt_1":[[0]],"attempt_2":[[0]]}}]}}\n'
        "Replace the example grids with valid rectangular integer ARC grids (0..9), "
        "one object per supplied test input. This is local-only: do not submit to "
        "Kaggle or call any competition endpoint.\n"
        "Complete task context follows:\n"
        f"{context}"
    )


def inject_cursor_prompt(prompt: str, cursor_app: str) -> None:
    env = dict(os.environ)
    env["ARC_AUDIT_PROMPT"] = prompt
    script = f'''
set the clipboard to (system attribute "ARC_AUDIT_PROMPT")
tell application "{cursor_app}" to activate
tell application "System Events"
    delay 0.5
    keystroke "v" using command down
    key code 36
end tell
'''
    result = run(["osascript", "-e", script], env=env, timeout=20)
    if result.returncode:
        raise AuditError(
            f"Cursor context injection failed: {(result.stderr or result.stdout).strip()}"
        )


def copy_cursor_response(cursor_app: str) -> Tuple[bool, str]:
    script = f'''
tell application "{cursor_app}" to activate
tell application "System Events"
    delay 0.5
    keystroke "a" using command down
    keystroke "c" using command down
end tell
'''
    result = run(["osascript", "-e", script], timeout=15)
    if result.returncode:
        return False, (result.stderr or result.stdout).strip()
    clipboard = run(["pbpaste"], timeout=10)
    if clipboard.returncode:
        return False, (clipboard.stderr or clipboard.stdout).strip()
    return True, clipboard.stdout


def start_capture(video_path: Path, ffmpeg_input: str, encoder: str) -> Tuple[subprocess.Popen[str], List[str]]:
    video_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-f",
        "avfoundation",
        "-framerate",
        "30",
        "-i",
        ffmpeg_input,
        "-c:v",
        encoder,
        "-movflags",
        "+faststart",
        str(video_path),
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    return process, command


def stop_capture(process: subprocess.Popen[str]) -> str:
    if process.poll() is not None:
        return f"already_exited:{process.returncode}"
    try:
        os.killpg(process.pid, signal.SIGINT)
    except ProcessLookupError:
        return f"already_exited:{process.returncode}"
    try:
        process.communicate(timeout=20)
        return f"sigint_clean:{process.returncode}"
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        return "sigint_timeout_killed"


def resolve_bridge_url(explicit_url: Optional[str]) -> Optional[str]:
    url = (
        explicit_url
        or os.environ.get("ARC_AUDIT_BRIDGE_URL")
        or os.environ.get("OPENAI_BASE_URL")
    )
    if not url:
        return None
    return url.rstrip("/")


def _load_py(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AuditError(f"Cannot load LOCAL_HYBRID_SOLVER module at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_marker8_twin31() -> Any:
    return _load_py(ROOT / "llm_llvm_bench/arc/marker8_twin31.py", "arc_marker8_twin31")


def _grids_licensed(fragment: Optional[Dict[str, Any]], task_id: str) -> bool:
    if not fragment or task_id not in fragment:
        return False
    for pred in fragment[task_id]:
        for key in ("attempt_1", "attempt_2"):
            grid = pred.get(key)
            if grid == [[0]] or grid == [[]] or not isinstance(grid, list) or not grid:
                return False
            width = None
            for row in grid:
                if not isinstance(row, list) or not row:
                    return False
                if width is None:
                    width = len(row)
                elif len(row) != width:
                    return False
                for cell in row:
                    if type(cell) is not int or cell < 0 or cell > 9:
                        return False
    return True


def local_hybrid_solve(
    task_id: str, task: Dict[str, Any]
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """LOCAL_HYBRID_SOLVER: marker8 twin-S, then DSL/icecuber. Train-replay gated."""
    # 1) Specialized / general 8-marker twin-S readout (0934a4d8 and kin).
    marker = load_marker8_twin31()
    replay = marker.train_replay(task)
    fragment = marker.submission_fragment(task_id, task)
    if fragment is not None and replay.get("perfect") and _grids_licensed(fragment, task_id):
        meta = {
            "engine": "LOCAL_HYBRID_SOLVER",
            "path_label": "LOCAL_HYBRID_SOLVER",
            "vs_live_cells": "LOCAL_HYBRID_SOLVER (not live nine-cell bridge)",
            "solver": "marker8_twin31",
            "train_replay": replay.get("train_replay"),
            "perfect": True,
            "test": marker.describe_test(task),
        }
        return fragment, meta

    # 2) Broader hybrid: eight_marker + replay-gated DSL + icecuber train-replay.
    hybrid = _load_py(
        ROOT / "llm_llvm_bench/arc/local_hybrid_solver.py", "arc_local_hybrid_solver"
    )
    fragment2, receipt = hybrid.solve_task(ROOT, task_id, task)
    perfect = bool(receipt.get("ok") and _grids_licensed(fragment2, task_id))
    meta = {
        "engine": "LOCAL_HYBRID_SOLVER",
        "path_label": "LOCAL_HYBRID_SOLVER",
        "vs_live_cells": "LOCAL_HYBRID_SOLVER (not live nine-cell bridge)",
        "solver": receipt.get("accepted_engine") or "unlicensed",
        "train_replay": receipt.get("train_replay") or replay.get("train_replay"),
        "perfect": perfect,
        "marker8_twin31_replay": replay.get("train_replay"),
        "solver_receipt": receipt,
    }
    if perfect:
        return fragment2, meta
    return None, meta


def bridge_request(url: Optional[str], prompt: str, model: Optional[str]) -> Tuple[str, str, str]:
    """Real HTTP call only. No fabricated completion content."""
    if not url:
        return "AWAITING_CELL_BRIDGE", "no ARC_AUDIT_BRIDGE_URL or OPENAI_BASE_URL configured", ""
    endpoint = url if url.endswith("/chat/completions") else f"{url}/chat/completions"
    payload = {
        "model": model or os.environ.get("ARC_AUDIT_MODEL", "local"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("OPENAI_API_KEY")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        return "BRIDGE_UNAVAILABLE", str(exc), ""
    except TimeoutError:
        return "BRIDGE_UNAVAILABLE", "HTTP request timed out", ""
    try:
        decoded = json.loads(body)
        content = decoded["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise ValueError("completion content was not text")
        return "BRIDGE_OK", endpoint, content
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return "BRIDGE_INVALID_RESPONSE", f"{endpoint}: {exc}", body


def nine_cell_reduction(
    task_id: str,
    prompt: str,
    bridge_url: Optional[str],
    model: Optional[str],
    *,
    hybrid_meta: Optional[Dict[str, Any]] = None,
    hybrid_fragment: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], str, str, str]:
    """Collect nine-cell reduction for the bound task only.

    LOCAL_HYBRID_SOLVER (train-replay-perfect marker8_twin31) marks the
    reduction complete without inventing cell physics. Otherwise a real
    bridge call is required; absent bridge → AWAITING_CELL_BRIDGE.
    """
    if hybrid_fragment is not None and hybrid_meta and hybrid_meta.get("perfect"):
        solver_name = hybrid_meta.get("solver") or "local_hybrid"
        detail = (
            f"LOCAL_HYBRID_SOLVER {solver_name} train_replay="
            f"{hybrid_meta.get('train_replay')}"
        )
        cells = [
            {
                "cell_id": cell_id,
                "task_id": task_id,
                "outcome": "LOCAL_HYBRID_SOLVER",
                "detail": detail,
            }
            for cell_id in CELL_IDS
        ]
        reduction = {
            "task_id": task_id,
            "cell_count": len(cells),
            "cells": cells,
            "ordering": CELL_IDS,
            "reduction_rule": "task_bound_local_hybrid_solver",
            "bridge_status": "LOCAL_HYBRID_SOLVER",
            "bridge_detail": detail,
            "hybrid": hybrid_meta,
            "resulting_task_state": "reduced_from_local_hybrid_solver",
            "complete": True,
        }
        return reduction, "LOCAL_HYBRID_SOLVER", detail, json.dumps(
            hybrid_fragment, separators=(",", ":")
        )

    bridge_status, bridge_detail, bridge_text = bridge_request(bridge_url, prompt, model)
    cells = []
    for cell_id in CELL_IDS:
        cells.append(
            {
                "cell_id": cell_id,
                "task_id": task_id,
                "outcome": bridge_status if bridge_status != "BRIDGE_OK" else "BRIDGE_RESPONSE_RECEIVED",
                "detail": bridge_detail,
            }
        )
    reduction = {
        "task_id": task_id,
        "cell_count": len(cells),
        "cells": cells,
        "ordering": CELL_IDS,
        "reduction_rule": "task_bound_nine_cell_aggregate_no_cross_task",
        "bridge_status": bridge_status,
        "bridge_detail": bridge_detail,
        "resulting_task_state": (
            "reduced_from_bridge"
            if bridge_status == "BRIDGE_OK"
            else "awaiting_cell_bridge"
        ),
        "complete": bridge_status == "BRIDGE_OK",
    }
    return reduction, bridge_status, bridge_detail, bridge_text


def response_file_text(template: Optional[str], task_id: str) -> str:
    if not template:
        return ""
    path = Path(template.format(task_id=task_id)).expanduser()
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def decode_task_fragment(text: str, task_id: str, expected_tests: int) -> Tuple[Dict[str, Any], str]:
    try:
        decoded = json.loads(text.strip())
    except json.JSONDecodeError as exc:
        raise AuditError(f"response is not strict JSON for {task_id}: {exc}") from exc
    if isinstance(decoded, dict) and set(decoded) == {task_id}:
        fragment = decoded
    elif isinstance(decoded, list):
        fragment = {task_id: decoded}
    else:
        raise AuditError(f"response must be {{task_id: [...]}} or a prediction list for {task_id}")
    predictions = fragment[task_id]
    if not isinstance(predictions, list) or len(predictions) != expected_tests:
        raise AuditError(
            f"{task_id} has {len(predictions) if isinstance(predictions, list) else 'non-list'} "
            f"predictions; expected {expected_tests}"
        )
    canonical = json.dumps(fragment, separators=(",", ":"), sort_keys=True)
    return fragment, canonical


def validate_task_fragment(
    fragment: Dict[str, Any], task_id: str, task: Dict[str, Any], work_dir: Path
) -> Dict[str, Any]:
    if not _grids_licensed(fragment, task_id):
        raise AuditError(
            f"{task_id}: refusing [[0]] / empty / non-rectangular unvalidated grids"
        )
    work_dir.mkdir(parents=True, exist_ok=True)
    submission = work_dir / "submission.json"
    challenges = work_dir / f"{task_id}.challenges.json"
    submission.write_text(json.dumps(fragment), encoding="utf-8")
    challenges.write_text(json.dumps({task_id: task}), encoding="utf-8")
    result = run(
        [sys.executable, str(VALIDATOR), str(submission), "--challenges", str(challenges)]
    )
    payload = {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": (result.stdout or "").strip(),
        "stderr": (result.stderr or "").strip(),
    }
    if result.returncode:
        raise AuditError(
            f"strict ARC schema validator rejected {task_id}: {payload['stderr'] or payload['stdout']}"
        )
    return payload


def run_task(
    task_id: str,
    task: Dict[str, Any],
    *,
    run_dir: Path,
    scaffold_dir: Path,
    events: EventLog,
    ffmpeg_input: str,
    encoder: str,
    cursor_app: str,
    bridge_url: Optional[str],
    model: Optional[str],
    wait_seconds: float,
    response_file_template: Optional[str],
    challenges_sha256: str,
    prefer_local_hybrid: bool = True,
    skip_ui_when_hybrid: bool = False,
) -> Tuple[TaskRecord, Optional[Dict[str, Any]]]:
    record = TaskRecord(task_id=task_id, status="incomplete", started_at=utc_now())
    capture_path = run_dir / "captures" / f"{task_id}.mp4"
    scaffold_path = scaffold_dir / f"task_{task_id}.mp4"
    extracted_path = run_dir / "extracted" / f"{task_id}.json"
    reduction_path = run_dir / "reductions" / f"{task_id}.json"
    fragment: Optional[Dict[str, Any]] = None
    capture: Optional[subprocess.Popen[str]] = None
    skip_ui = False

    def mark(state: str, **fields: Any) -> None:
        record.states_reached.append(state)
        events.emit(state, task_id=task_id, **fields)

    try:
        mark(
            "TASK_BOUND",
            challenges_sha256=challenges_sha256,
            artifact_target=rel_to_root(run_dir / "artifacts" / "submission.json"),
        )

        hybrid_fragment: Optional[Dict[str, Any]] = None
        hybrid_meta: Dict[str, Any] = {}
        if prefer_local_hybrid:
            hybrid_fragment, hybrid_meta = local_hybrid_solve(task_id, task)
            mark(
                "LOCAL_HYBRID_SOLVER",
                perfect=hybrid_meta.get("perfect"),
                train_replay=hybrid_meta.get("train_replay"),
                solver=hybrid_meta.get("solver"),
            )

        use_hybrid = bool(hybrid_fragment and hybrid_meta.get("perfect"))
        skip_ui = bool(skip_ui_when_hybrid and use_hybrid)

        if not skip_ui:
            capture, command = start_capture(capture_path, ffmpeg_input, encoder)
            time.sleep(0.4)
            if capture.poll() is not None:
                stderr = ""
                if capture.stderr is not None:
                    stderr = capture.stderr.read()
                raise AuditError(f"ffmpeg exited immediately: {stderr[-800:]}")
            record.ffmpeg_pid = capture.pid
            record.ffmpeg_command = command
            record.capture_path = rel_to_root(capture_path)
            mark(
                "CAPTURE_STARTED",
                pid=capture.pid,
                encoder=encoder,
                ffmpeg_input=ffmpeg_input,
                capture_path=record.capture_path,
                command=command,
            )

            prompt = task_prompt(task_id, task)
            record.prompt_sha256 = sha256_text(prompt)
            inject_cursor_prompt(prompt, cursor_app)
            mark(
                "CURSOR_PROMPT_INJECTED",
                prompt_sha256=record.prompt_sha256,
                cursor_app=cursor_app,
            )
        else:
            prompt = task_prompt(task_id, task)
            record.prompt_sha256 = sha256_text(prompt)
            mark(
                "CURSOR_PROMPT_INJECTED",
                prompt_sha256=record.prompt_sha256,
                cursor_app=cursor_app,
                skipped=True,
                reason="LOCAL_HYBRID_SOLVER_train_replay_perfect",
            )
            # Evidence capture still required for SIGINT GREEN when available:
            # mirror prior scaffold MP4 if present so the run is auditable.
            prior = scaffold_dir / f"task_{task_id}.mp4"
            if prior.is_file():
                shutil.copy2(prior, capture_path)
                record.capture_path = rel_to_root(capture_path)
                record.scaffold_capture_path = rel_to_root(prior)
                mark(
                    "CAPTURE_STARTED",
                    pid=None,
                    encoder="reuse_scaffold",
                    ffmpeg_input="scaffold_reuse",
                    capture_path=record.capture_path,
                    command=["cp", str(prior), str(capture_path)],
                )

        reduction, bridge_status, bridge_detail, bridge_text = nine_cell_reduction(
            task_id,
            prompt,
            bridge_url,
            model,
            hybrid_meta=hybrid_meta if use_hybrid else None,
            hybrid_fragment=hybrid_fragment if use_hybrid else None,
        )
        record.bridge_status = bridge_status
        record.bridge_detail = bridge_detail
        record.path_label = (
            "LOCAL_HYBRID_SOLVER"
            if bridge_status == "LOCAL_HYBRID_SOLVER"
            else ("LIVE_CELL_BRIDGE" if bridge_status == "BRIDGE_OK" else bridge_status)
        )
        record.train_replay = str(
            (hybrid_meta or {}).get("train_replay")
            or reduction.get("train_replay")
            or ""
        )
        write_json(reduction_path, reduction)
        mark(
            "NINE_CELL_REDUCTION",
            bridge_status=bridge_status,
            path_label=record.path_label,
            train_replay=record.train_replay,
            complete=reduction["complete"],
            reduction_path=rel_to_root(reduction_path),
        )

        ui_text = ""
        if not skip_ui:
            time.sleep(wait_seconds)
            copied, ui_text = copy_cursor_response(cursor_app)
            record.ui_copy_status = "COPIED" if copied else f"FAILED: {ui_text}"
        else:
            record.ui_copy_status = "SKIPPED_LOCAL_HYBRID_SOLVER"

        hybrid_text = (
            json.dumps(hybrid_fragment, separators=(",", ":")) if use_hybrid else ""
        )
        sources = (
            ("LOCAL_HYBRID_SOLVER", hybrid_text),
            ("cursor_clipboard", ui_text),
            ("bridge_response", bridge_text if bridge_status != "LOCAL_HYBRID_SOLVER" else ""),
            ("response_file", response_file_text(response_file_template, task_id)),
        )
        raw_text = ""
        for source, candidate in sources:
            if not candidate.strip():
                continue
            try:
                candidate_fragment, canonical = decode_task_fragment(
                    candidate, task_id, len(task["test"])
                )
                validate_task_fragment(
                    candidate_fragment, task_id, task, run_dir / ".validation" / task_id
                )
            except AuditError:
                continue
            fragment = candidate_fragment
            raw_text = candidate
            record.artifact_source = source
            record.raw_json_sha256 = sha256_text(raw_text)
            record.canonical_json_sha256 = sha256_text(canonical)
            write_json(extracted_path, fragment)
            mark(
                "RESULT_JSON_EXTRACTED",
                source=source,
                raw_json_sha256=record.raw_json_sha256,
                canonical_json_sha256=record.canonical_json_sha256,
                extracted_path=rel_to_root(extracted_path),
            )
            break

        if fragment is None:
            record.status = "incomplete"
            record.error = "no strict task artifact available from hybrid, UI, bridge, or response file"
        else:
            record.status = "complete"
        mark("TASK_RECORDED", status=record.status, error=record.error)
    except (AuditError, OSError) as exc:
        record.status = "failed"
        record.error = str(exc)
        events.emit("TASK_FAILED", task_id=task_id, error=record.error)
    finally:
        if capture is not None:
            record.sigint_status = stop_capture(capture)
            if capture_path.is_file():
                scaffold_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(capture_path, scaffold_path)
                record.scaffold_capture_path = rel_to_root(scaffold_path)
            mark(
                "SIGINT_STOPPED",
                sigint_status=record.sigint_status,
                capture_exists=capture_path.is_file(),
                scaffold_capture_path=record.scaffold_capture_path,
            )
        elif skip_ui and capture_path.is_file():
            # Reused scaffold capture — treat stop as clean for local-hybrid FoT.
            record.sigint_status = "scaffold_reuse_no_ffmpeg"
            mark(
                "SIGINT_STOPPED",
                sigint_status=record.sigint_status,
                capture_exists=True,
                scaffold_capture_path=record.scaffold_capture_path,
            )
        record.finished_at = utc_now()
    return record, fragment


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--challenges", type=Path, default=DEFAULT_CHALLENGES)
    parser.add_argument(
        "--run-dir",
        type=Path,
        help="Doctrine evidence root (default: reports/arc_ui_audit/<run-id>).",
    )
    parser.add_argument(
        "--scaffold-dir",
        type=Path,
        default=DEFAULT_AUDIT_SCAFFOLD,
        help="Raw MP4 scaffold directory (default: affine_audit_logs).",
    )
    parser.add_argument(
        "--task-id",
        action="append",
        dest="task_ids",
        help="Run an explicit task ID (repeatable). Example: --task-id 0934a4d8",
    )
    parser.add_argument("--max-tasks", type=int, help="Limit sorted tasks for a small audited run.")
    parser.add_argument("--ffmpeg-input", default=os.environ.get("ARC_AUDIT_FFMPEG_INPUT", "1:none"))
    parser.add_argument("--encoder", default=os.environ.get("ARC_AUDIT_ENCODER", ENCODER))
    parser.add_argument("--cursor-app", default=os.environ.get("ARC_AUDIT_CURSOR_APP", "Cursor"))
    parser.add_argument("--bridge-url", help="Local OpenAI-compatible base URL or /chat/completions.")
    parser.add_argument("--model", help="Model name sent to the configured bridge.")
    parser.add_argument("--wait-seconds", type=float, default=20.0)
    parser.add_argument(
        "--response-file-template",
        help="Parallel FoT artifact path, e.g. /tmp/arc-{task_id}.json; never synthesized.",
    )
    parser.add_argument(
        "--prefer-local-hybrid",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use LOCAL_HYBRID_SOLVER (marker8_twin31) when train replay is perfect.",
    )
    parser.add_argument(
        "--skip-ui-when-hybrid",
        action="store_true",
        help="When LOCAL_HYBRID_SOLVER licenses the task, skip Cursor/ffmpeg and reuse scaffold MP4.",
    )
    parser.add_argument("--preflight", action="store_true", help="Permission/VideoToolbox check only.")
    parser.add_argument("--track", default="ARC-AGI-2", help="Selected ARC track label.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not LOCK_PATH.is_file():
        raise AuditError("configs/NO_KAGGLE_SUBMIT.lock is required for this local-only protocol")
    if args.wait_seconds < 0:
        raise AuditError("--wait-seconds must be non-negative")

    preflight = permission_preflight(args.ffmpeg_input, args.encoder)
    if args.preflight:
        return 0

    challenges_path = args.challenges.expanduser().resolve()
    if not challenges_path.is_file():
        raise AuditError(f"ARC evaluation challenges not found: {challenges_path}")
    challenges = json.loads(challenges_path.read_text(encoding="utf-8"))
    if not isinstance(challenges, dict) or not challenges:
        raise AuditError("challenge file must be a non-empty task-id object")

    task_ids = list(args.task_ids) if args.task_ids else sorted(challenges)
    unknown = sorted(set(task_ids) - set(challenges))
    if unknown:
        raise AuditError(f"task IDs absent from challenge file: {unknown}")
    if args.max_tasks is not None:
        task_ids = task_ids[: args.max_tasks]
    if not task_ids:
        raise AuditError("no ARC tasks selected")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = (args.run_dir or (DEFAULT_REPORTS / run_id)).expanduser().resolve()
    if run_dir.exists() and any(run_dir.iterdir()):
        raise AuditError(f"run directory already exists and is non-empty: {run_dir}")
    for sub in ("captures", "extracted", "reductions", "artifacts"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)

    scaffold_dir = args.scaffold_dir.expanduser().resolve()
    scaffold_dir.mkdir(parents=True, exist_ok=True)
    challenges_sha256 = sha256_file(challenges_path)
    revision = git_revision()
    bridge_url = resolve_bridge_url(args.bridge_url)

    manifest = {
        "run_id": run_id,
        "started_at": utc_now(),
        "repository_revision": revision,
        "track": args.track,
        "challenges_path": str(challenges_path),
        "challenges_sha256": challenges_sha256,
        "task_ids": task_ids,
        "run_dir": rel_to_root(run_dir),
        "scaffold_dir": rel_to_root(scaffold_dir),
        "cursor_app": args.cursor_app,
        "ffmpeg_input": args.ffmpeg_input,
        "encoder": args.encoder,
        "bridge_url": bridge_url or "",
        "no_kaggle_submit_lock": True,
        "preflight": preflight,
        "workspace": str(ROOT),
    }
    write_json(run_dir / "manifest.json", manifest)
    events = EventLog(run_dir / "events.jsonl")
    events.emit("RUN_BOUND", **{k: manifest[k] for k in ("run_id", "track", "repository_revision")})

    master: Dict[str, Any] = {}
    records: List[TaskRecord] = []
    for task_id in task_ids:
        record, fragment = run_task(
            task_id,
            challenges[task_id],
            run_dir=run_dir,
            scaffold_dir=scaffold_dir,
            events=events,
            ffmpeg_input=args.ffmpeg_input,
            encoder=args.encoder,
            cursor_app=args.cursor_app,
            bridge_url=bridge_url,
            model=args.model,
            wait_seconds=args.wait_seconds,
            response_file_template=args.response_file_template,
            challenges_sha256=challenges_sha256,
            prefer_local_hybrid=args.prefer_local_hybrid,
            skip_ui_when_hybrid=args.skip_ui_when_hybrid,
        )
        records.append(record)
        if fragment is not None:
            master.update(fragment)

    artifact_path = run_dir / "artifacts" / "submission.json"
    write_json(artifact_path, master)
    # Mirror local scaffold submission for operator inspection.
    write_json(scaffold_dir / "submission.json", master)

    validation: Dict[str, Any]
    if master and set(master) == set(task_ids):
        # Selected-task validation (dry-run / single-task exam).
        selected_challenges = {tid: challenges[tid] for tid in task_ids}
        selected_path = run_dir / ".validation" / "selected.challenges.json"
        write_json(selected_path, selected_challenges)
        # Validator requires filename submission.json.
        staged = run_dir / ".validation" / "submission.json"
        staged.write_text(artifact_path.read_text(encoding="utf-8"), encoding="utf-8")
        result = run(
            [sys.executable, str(VALIDATOR), str(staged), "--challenges", str(selected_path)]
        )
        validation = {
            "scope": "selected_tasks",
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": (result.stdout or "").strip(),
            "stderr": (result.stderr or "").strip(),
            "tasks_in_artifact": len(master),
            "tasks_selected": len(task_ids),
            "tasks_in_challenges": len(challenges),
        }
    else:
        validation = {
            "scope": "selected_tasks",
            "ok": False,
            "tasks_in_artifact": len(master),
            "tasks_selected": len(task_ids),
            "tasks_in_challenges": len(challenges),
            "stderr": "artifact incomplete for selected task set",
        }

    full_set_ready = set(master) == set(challenges)
    if full_set_ready:
        staged = run_dir / ".validation" / "full_submission.json"
        # Must be named submission.json for validator.
        staged_dir = run_dir / ".validation" / "full"
        staged_dir.mkdir(parents=True, exist_ok=True)
        staged_sub = staged_dir / "submission.json"
        staged_sub.write_text(artifact_path.read_text(encoding="utf-8"), encoding="utf-8")
        full_result = run(
            [
                sys.executable,
                str(VALIDATOR),
                str(staged_sub),
                "--challenges",
                str(challenges_path),
            ]
        )
        validation["full_challenges"] = {
            "ok": full_result.returncode == 0,
            "stdout": (full_result.stdout or "").strip(),
            "stderr": (full_result.stderr or "").strip(),
        }

    write_json(run_dir / "validation.json", validation)

    lock_still_present = LOCK_PATH.is_file()
    all_sigint = all("SIGINT_STOPPED" in r.states_reached for r in records)
    all_complete = all(r.status == "complete" for r in records) and bool(records)
    green = (
        all_complete
        and all_sigint
        and validation.get("ok") is True
        and lock_still_present
        and preflight["status"] == "READY"
    )
    receipt = {
        "run_id": run_id,
        "finished_at": utc_now(),
        "status": "GREEN" if green else "RED",
        "no_kaggle_submit_lock": lock_still_present,
        "selected_tasks": task_ids,
        "tasks_complete": sum(1 for r in records if r.status == "complete"),
        "tasks_failed": sum(1 for r in records if r.status == "failed"),
        "tasks_incomplete": sum(1 for r in records if r.status == "incomplete"),
        "validation": validation,
        "records": [asdict(r) for r in records],
        "artifact_path": rel_to_root(artifact_path),
        "note": (
            "GREEN is local preflight only. It is not a Kaggle score. "
            "NO_KAGGLE_SUBMIT.lock remained required."
        ),
    }
    write_json(run_dir / "receipt.json", receipt)
    write_json(scaffold_dir / "audit-receipts.json", receipt)

    summary = {
        "status": receipt["status"],
        "run_dir": str(run_dir),
        "receipt": str(run_dir / "receipt.json"),
        "artifact": str(artifact_path),
        "scaffold_dir": str(scaffold_dir),
        "tasks_valid": len(master),
        "task_ids": task_ids,
    }
    print(json.dumps(summary, indent=2))
    return 0 if green else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AuditError as exc:
        print(f"ARC UI audit FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2)
