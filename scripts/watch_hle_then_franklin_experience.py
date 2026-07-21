#!/usr/bin/env python3
"""Park Franklin LLM until HLE frees a :8080 slot, then resume experience batch.

Never kills HLE. Merges wave5/skip-llm lifts and rebuilds notebook on climb.
No Kaggle submit.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRED = ROOT / "harnesses/hle/hle_eval/hle_qwen3.6-35b-a3b.json"
HLE_PID_HINT = 27815
OUT = ROOT / "reports/airgap_agi2_franklin_s4_experience_llm_resume"
IDS = ROOT / "reports/airgap_agi2_franklin_s4_experience_zoom/task_ids.json"
LOG = ROOT / "reports/watch_hle_franklin.log"
PY = os.environ.get(
    "PYTHON",
    "/Applications/Xcode-Beta.app/Contents/Developer/Library/Frameworks/"
    "Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python",
)


def log(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def hle_pred_count() -> int:
    if not PRED.is_file():
        return -1
    try:
        return len(json.loads(PRED.read_text(encoding="utf-8")))
    except Exception:
        return -1


def hle_alive() -> bool:
    if Path(f"/proc/{HLE_PID_HINT}").exists():  # linux
        return True
    r = subprocess.run(
        ["kill", "-0", str(HLE_PID_HINT)],
        capture_output=True,
    )
    if r.returncode == 0:
        return True
    r = subprocess.run(
        ["pgrep", "-f", "hle_eval/run_model_predictions"],
        capture_output=True,
        text=True,
    )
    return bool(r.stdout.strip())


def slot8080_clients() -> tuple[int, set[int]]:
    """Return (client_count, set of client PIDs talking to :8080)."""
    r = subprocess.run(
        ["lsof", "-nP", "-iTCP:8080", "-sTCP:ESTABLISHED"],
        capture_output=True,
        text=True,
    )
    pids: set[int] = set()
    for line in r.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 9:
            continue
        # client side: local port != 8080
        name = parts[-1]
        try:
            pid = int(parts[1])
        except ValueError:
            continue
        if "->127.0.0.1:8080" in name or "->localhost:8080" in name:
            pids.add(pid)
    return len(pids), pids


def merge_licensed() -> int:
    r = subprocess.run(
        [PY, str(ROOT / "scripts/merge_agi2_licensed_airgap.py"), "--root", str(ROOT), "--rebuild-notebook"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    lic = -1
    for line in (r.stdout + r.stderr).splitlines():
        if "MERGED licensed=" in line:
            log(line.strip())
            try:
                lic = int(line.split("licensed=")[1].split("/")[0])
            except Exception:
                pass
        if "REBUILD" in line or "SKIP rebuild" in line:
            log(line.strip())
    return lic


def franklin_llm_running() -> bool:
    r = subprocess.run(
        ["pgrep", "-fl", "build_agi2_franklin_s4_experience_batch"],
        capture_output=True,
        text=True,
    )
    for line in r.stdout.splitlines():
        if "--skip-llm" in line:
            continue
        if "build_agi2_franklin_s4_experience_batch" in line:
            return True
    return False


def resume_franklin() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if not IDS.is_file():
        # fall back to identity list from merge receipt
        rec = ROOT / "reports/airgap_agi2_test_20260721T175400Z/MERGED_LICENSED_VS_IDENTITY.json"
        ids = json.loads(rec.read_text())["identity_task_ids"]
        IDS.write_text(json.dumps(ids), encoding="utf-8")
    env = os.environ.copy()
    env["FRANKLIN_TIMEOUT"] = "360"
    env["FRANKLIN_MAX_TOKENS"] = "1000"
    log_path = OUT / "build.log"
    with log_path.open("a", encoding="utf-8") as fh:
        proc = subprocess.Popen(
            [
                PY,
                "-u",
                str(ROOT / "scripts/build_agi2_franklin_s4_experience_batch.py"),
                "--root",
                str(ROOT),
                "--out-dir",
                str(OUT),
                "--task-ids-file",
                str(IDS),
                "--experience-limit",
                "120",
                "--timeout",
                "360",
                "--max-turns",
                "4",
                "--limit",
                "24",
            ],
            cwd=str(ROOT),
            env=env,
            stdout=fh,
            stderr=subprocess.STDOUT,
        )
    (OUT / "pid.txt").write_text(str(proc.pid), encoding="utf-8")
    log(f"FRANKLIN_RESUMED pid={proc.pid} out={OUT} limit=24 timeout=360")
    return proc.pid


def main() -> int:
    log("WATCH start — park Franklin until HLE frees >=1 :8080 slot")
    last_pred = hle_pred_count()
    frank_started = False
    while True:
        pred = hle_pred_count()
        alive = hle_alive()
        ncli, pids = slot8080_clients()
        lic = merge_licensed()
        log(
            f"poll hle_alive={alive} preds={pred}/2500 "
            f"8080_clients={ncli} pids={sorted(pids)} "
            f"licensed={lic}/259 frank_running={franklin_llm_running()}"
        )
        # Resume when: HLE dead/finished OR fewer than 4 clients to :8080
        # OR preds stalled and clients < 4
        free_slot = ncli < 4
        hle_done = (not alive) or (pred >= 2500)
        stalled = pred == last_pred and pred >= 0
        if not frank_started and not franklin_llm_running():
            if hle_done or free_slot:
                resume_franklin()
                frank_started = True
            elif stalled and ncli <= 3:
                resume_franklin()
                frank_started = True
        last_pred = pred
        # Exit watch if franklin done and hle done
        if frank_started and not franklin_llm_running() and hle_done:
            merge_licensed()
            log("WATCH done — franklin finished and HLE complete")
            return 0
        time.sleep(60)


if __name__ == "__main__":
    raise SystemExit(main())
