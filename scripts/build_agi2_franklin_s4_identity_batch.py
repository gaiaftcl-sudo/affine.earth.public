#!/usr/bin/env python3
"""Franklin S4 batch on AGI-2 test identity residue. Train-replay gate only.

Writes submission.partial.json with LICENSED grids (attempt_1 != test input).
No Kaggle submit. Orthogonal to icecuber hybrid waves.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from llm_llvm_bench.arc.franklin_s4_projection import (  # noqa: E402
    jordan_loop_bound_closed,
    projection_system_prompt,
    wrapper_evidence,
)
from llm_llvm_bench.arc.franklin_uum8d_system_prompt import (  # noqa: E402
    franklin_uum8d_game_comprehension_system_prompt,
)
from llm_llvm_bench.exam.miss_reinjection import (  # noqa: E402
    load_learned_experiences,
)

Grid = List[List[int]]


def grid_str(grid: Grid) -> str:
    return "\n".join("".join(str(c) for c in row) for row in grid)


def parse_grid(text: Any) -> Optional[Grid]:
    if isinstance(text, list):
        if text and isinstance(text[0], list):
            try:
                return [[int(c) for c in row] for row in text]
            except Exception:
                return None
        return None
    if not isinstance(text, str):
        return None
    rows = [r.strip() for r in text.strip().splitlines() if r.strip()]
    if not rows:
        return None
    try:
        grid = [[int(ch) for ch in row if ch.isdigit()] for row in rows]
    except Exception:
        return None
    if not grid or not all(grid) or len({len(r) for r in grid}) != 1:
        return None
    if any(c < 0 or c > 9 for row in grid for c in row):
        return None
    return grid


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None


def train_replay_ok(payload: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
    preds = payload.get("train_predictions")
    if preds is None:
        s4 = payload.get("s4") or {}
        typed = s4.get("typed_candidate") or {}
        preds = typed.get("train_predictions")
    if not isinstance(preds, list):
        return {"perfect": False, "passed": 0, "total": len(task["train"])}
    ok = 0
    for i, ex in enumerate(task["train"]):
        got = parse_grid(preds[i]) if i < len(preds) else None
        if got == ex["output"]:
            ok += 1
    return {
        "perfect": ok == len(task["train"]),
        "passed": ok,
        "total": len(task["train"]),
    }


def extract_test_preds(
    payload: Dict[str, Any], task: Dict[str, Any]
) -> Optional[List[Dict[str, Grid]]]:
    raw = payload.get("test_predictions") or payload.get("test_outputs")
    s4 = payload.get("s4") or {}
    typed = s4.get("typed_candidate") or {}
    if raw is None:
        raw = typed.get("test_predictions") or typed.get("outputs")
    if raw is None:
        return None
    if isinstance(raw, dict):
        raw = [raw.get(str(i), raw.get(i)) for i in range(len(task["test"]))]
    if not isinstance(raw, list) or len(raw) < len(task["test"]):
        return None
    out: List[Dict[str, Grid]] = []
    for i, case in enumerate(task["test"]):
        item = raw[i]
        a1 = a2 = None
        if isinstance(item, dict):
            a1 = parse_grid(item.get("attempt_1") or item.get("output") or item.get("grid"))
            a2 = parse_grid(item.get("attempt_2") or item.get("attempt_1") or item.get("output"))
        else:
            a1 = parse_grid(item)
            a2 = a1
        if a1 is None:
            return None
        if a2 is None:
            a2 = [list(r) for r in a1]
        out.append({"attempt_1": a1, "attempt_2": a2})
    return out


def _zoom_move(task: Dict[str, Any]) -> str:
    """Usual puzzle move: zoom in/out from train shape shear."""
    zooms = []
    for ex in task["train"]:
        ih, iw = len(ex["input"]), len(ex["input"][0])
        oh, ow = len(ex["output"]), len(ex["output"][0])
        if oh * ow < ih * iw:
            zooms.append("zoom_in_crop")
        elif oh * ow > ih * iw:
            zooms.append("zoom_out_expand")
        elif (oh, ow) == (ih, iw):
            zooms.append("same_canvas_rewrite")
        else:
            zooms.append("reshape")
    if not zooms:
        return "same_canvas_rewrite"
    # majority hint
    return max(set(zooms), key=zooms.count)


def solve_one(
    session: requests.Session,
    base: str,
    key: str,
    model: str,
    tid: str,
    task: Dict[str, Any],
    max_turns: int,
    timeout: int,
    learned_experiences: List[Dict[str, Any]],
) -> Dict[str, Any]:
    train_pack = []
    for i, ex in enumerate(task["train"]):
        train_pack.append(
            {
                "i": i,
                "in_shape": [len(ex["input"]), len(ex["input"][0])],
                "out_shape": [len(ex["output"]), len(ex["output"][0])],
                "input": grid_str(ex["input"]),
                "output": grid_str(ex["output"]),
            }
        )
    test_pack = []
    for i, case in enumerate(task["test"]):
        test_pack.append(
            {
                "i": i,
                "in_shape": [len(case["input"]), len(case["input"][0])],
                "input": grid_str(case["input"]),
            }
        )
    zoom = _zoom_move(task)
    # Compact experience cards for the prompt (engines + invariants, not full grids)
    experience_cards = [
        {
            "task_id": e.get("task_id"),
            "engine": e.get("engine"),
            "status": e.get("status"),
            "c4_invariant": str(e.get("c4_invariant") or "")[:180],
            "grammar_update": str(e.get("grammar_update") or "")[:120],
        }
        for e in learned_experiences[:8]
    ]
    system = (
        projection_system_prompt(franklin_uum8d_game_comprehension_system_prompt())
        + f"""
You are solving ARC-AGI-2 Kaggle TEST task {tid}.
Jordan loop bound: LOCKED only after demonstration_replay perfect on ALL trains.
Pull LEARNED_CLOSED_EXPERIENCES before inventing a new rule. Usual move: {zoom}.
CRITICAL: Reply with ONE JSON object only. No markdown. No <think>.
Required keys:
  task_id, train_predictions, test_predictions, reused_experience_task_id
train_predictions: list of digit-string grids (newline rows) matching EVERY train output exactly.
test_predictions: list of {{attempt_1, attempt_2}} digit-string grids for each test input.
attempt_1 MUST differ from the test input when a real rule is found.
Keep JSON under 3500 characters.
"""
    )
    messages = [{"role": "system", "content": system}]
    evidence = wrapper_evidence(
        track="arc2",
        item_id=tid,
        answer_contract="typed_output_grid; LOCKED only after demonstration_replay (Jordan loop closed)",
        s1={
            "task_id": tid,
            "train": train_pack,
            "test": test_pack,
            "zoom_move": zoom,
            "learned_experience_count": len(experience_cards),
        },
        s2={
            "candidates": ["geometry rewrite", "color map", "object transform", zoom],
            "learned_experiences": experience_cards,
        },
        s3={
            "next_check": "demonstration_replay all trains then emit test_predictions",
            "jordan_loop_bound": "LOCKED forbidden until zero remainder against C4",
            "validator": "demonstration_replay",
        },
        prior_gate={"result": "S4_REINJECT", "jordan_loop_bound_open": True},
    )
    evidence["learned_experiences"] = experience_cards
    evidence["invariant"] = "pull_learned_experiences_every_play"
    messages.append(
        {
            "role": "user",
            "content": json.dumps(
                {
                    "WRAPPER_EVIDENCE": evidence,
                    "LEARNED_CLOSED_EXPERIENCES": experience_cards,
                    "instruction": (
                        "Reuse a closed experience engine/invariant if it fits; "
                        "else invent via zoom move. Close Jordan loop via "
                        "perfect train replay before emitting test_predictions."
                    ),
                },
                sort_keys=True,
            ),
        }
    )
    last_replay: Dict[str, Any] = {"perfect": False}
    preds = None
    for turn in range(max_turns):
        try:
            response = session.post(
                f"{base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "temperature": 0.2,
                    "max_tokens": 2200,
                    "messages": messages,
                },
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()
            message = payload["choices"][0]["message"]
            answer = str(
                message.get("content") or message.get("reasoning_content") or ""
            ).strip()
        except Exception as exc:  # noqa: BLE001
            return {
                "task_id": tid,
                "ok": False,
                "error": str(exc),
                "turns": turn,
                "experiences_pulled": len(experience_cards),
            }
        messages.append({"role": "assistant", "content": answer})
        parsed = extract_json(answer)
        if not parsed:
            messages.append(
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "gate": "UNPARSED",
                            "instruction": "Reply with ONE JSON object only.",
                            "LEARNED_CLOSED_EXPERIENCES": experience_cards,
                        }
                    ),
                }
            )
            continue
        last_replay = train_replay_ok(parsed, task)
        perfect = bool(last_replay.get("perfect"))
        ratio = f"{last_replay.get('passed', 0)}/{last_replay.get('total', 0)}"
        bound = jordan_loop_bound_closed(
            "arc2",
            {
                "accepted": perfect,
                "train_replay": ratio,
                "detail": "train_replay_perfect" if perfect else "train_replay_miss",
            },
            accepted=perfect,
        )
        if perfect and bound.get("closed"):
            preds = extract_test_preds(parsed, task)
            if preds is not None:
                return {
                    "task_id": tid,
                    "ok": True,
                    "predictions": preds,
                    "turns": turn + 1,
                    "replay": last_replay,
                    "jordan_loop_bound": bound,
                    "experiences_pulled": len(experience_cards),
                    "reused_experience_task_id": parsed.get("reused_experience_task_id"),
                    "zoom_move": zoom,
                }
        messages.append(
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "gate": "S4_REINJECT",
                        "replay": last_replay,
                        "jordan_loop_bound": bound,
                        "LEARNED_CLOSED_EXPERIENCES": experience_cards,
                        "zoom_move": zoom,
                        "instruction": (
                            "Jordan loop still open or missing test_predictions. "
                            "Pull a CLOSED experience, apply zoom move, revise. "
                            "train_predictions must match demos exactly."
                        ),
                    }
                ),
            }
        )
    return {
        "task_id": tid,
        "ok": False,
        "turns": max_turns,
        "replay": last_replay,
        "experiences_pulled": len(experience_cards),
        "zoom_move": zoom,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--task-ids-file", type=Path, required=True)
    parser.add_argument("--max-turns", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--limit", type=int, default=0, help="0 = all")
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    base = os.environ.get("FRANKLIN_S4_BASE_URL", "http://127.0.0.1:8080/v1").rstrip("/")
    key = os.environ.get("OPENAI_API_KEY", "uum8d-hle-verifier")
    model = os.environ.get("FRANKLIN_S4_MODEL", "qwen/qwen3.6-35b-a3b")

    challenges = json.loads(
        (root / "data/arc-prize-2026-agi-2/arc-agi_test_challenges.json").read_text()
    )
    ids = json.loads(args.task_ids_file.read_text())
    if args.limit > 0:
        ids = ids[: args.limit]

    submission: Dict[str, Any] = {}
    receipts: Dict[str, Any] = {}
    partial = out / "submission.partial.json"
    receipt_path = out / "receipts.partial.json"
    if partial.is_file():
        submission = json.loads(partial.read_text())
        receipts = json.loads(receipt_path.read_text()) if receipt_path.is_file() else {}
        print(f"RESUME done={len(submission)}/{len(ids)}", flush=True)

    session = requests.Session()
    t0 = time.time()
    pending = [t for t in ids if t not in submission]
    state_dir = root / "reports" / "exam_reinjection"
    print(
        f"START franklin_s4 pending={len(pending)} model={model} base={base} "
        f"experience_state={state_dir}",
        flush=True,
    )
    for n, tid in enumerate(pending, 1):
        # Every play pulls learned CLOSED / LOCKED experiences (Jordan invariant).
        experiences = load_learned_experiences(
            state_dir,
            track="arc2",
            exclude_task_id=tid,
            limit=8,
        )
        result = solve_one(
            session,
            base,
            key,
            model,
            tid,
            challenges[tid],
            args.max_turns,
            args.timeout,
            experiences,
        )
        receipts[tid] = {
            k: v for k, v in result.items() if k != "predictions"
        }
        if result.get("ok") and result.get("predictions"):
            preds = result["predictions"]
            licensed = sum(
                1
                for i, p in enumerate(preds)
                if p["attempt_1"] != challenges[tid]["test"][i]["input"]
            )
            if licensed > 0:
                submission[tid] = preds
                receipts[tid]["licensed_grids"] = licensed
            else:
                receipts[tid]["ok"] = False
                receipts[tid]["reason"] = "identity_after_lock"
        partial.write_text(json.dumps(submission, separators=(",", ":")), encoding="utf-8")
        receipt_path.write_text(json.dumps(receipts, indent=2) + "\n", encoding="utf-8")
        lic = sum(
            1
            for tid2, preds in submission.items()
            for i, p in enumerate(preds)
            if p["attempt_1"] != challenges[tid2]["test"][i]["input"]
        )
        print(
            f"progress {n}/{len(pending)} stored={len(submission)} "
            f"licensed_grids={lic} ok={result.get('ok')} "
            f"elapsed={time.time()-t0:.0f}s tid={tid}",
            flush=True,
        )

    (out / "submission.json").write_text(
        json.dumps(submission, separators=(",", ":")), encoding="utf-8"
    )
    print(
        f"DONE franklin_s4 tasks_stored={len(submission)} → {out / 'submission.json'}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
