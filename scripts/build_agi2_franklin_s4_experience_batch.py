#!/usr/bin/env python3
"""Experience-backed Franklin S4 on AGI-2 platform identity residue.

Every play:
  1) load_learned_experiences (CLOSED seals from reports/exam_reinjection)
  2) rank by train IO fingerprint vs eval CLOSED tasks
  3) Franklin S4 propose with Jordan-loop bound in prompt
  4) local demonstration_replay gate on train_predictions
  5) accept test_predictions only when Jordan bound closed AND attempt_1 ≠ input

No Kaggle submit. Orthogonal to blind grammar rediscovery.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from llm_llvm_bench.arc.franklin_s4_projection import (  # noqa: E402
    exam_s4_user_prompt,
    jordan_loop_bound_closed,
    projection_system_prompt,
    build_miss_wrapper_evidence,
)
from llm_llvm_bench.arc.franklin_uum8d_system_prompt import (  # noqa: E402
    franklin_uum8d_game_comprehension_system_prompt,
)
from llm_llvm_bench.exam.miss_reinjection import (  # noqa: E402
    TRACK_ARC2,
    load_learned_experiences,
)

Grid = List[List[int]]


def grid_str(grid: Grid) -> str:
    return "\n".join("".join(str(c) for c in row) for row in grid)


def parse_grid(text: Any) -> Optional[Grid]:
    if isinstance(text, list) and text and isinstance(text[0], list):
        try:
            g = [[int(c) for c in row] for row in text]
        except Exception:
            return None
        if g and all(g) and len({len(r) for r in g}) == 1:
            return g
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
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            return None
        try:
            parsed = json.loads(m.group(0))
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None


def fingerprint(task: Dict[str, Any]) -> Tuple:
    feats = []
    for ex in task.get("train", []):
        inp, out = ex["input"], ex["output"]
        ih, iw = len(inp), len(inp[0]) if inp else 0
        oh, ow = len(out), len(out[0]) if out else 0
        ic = len({c for row in inp for c in row})
        oc = len({c for row in out for c in row})
        feats.append((ih, iw, oh, ow, ic, oc, oh - ih, ow - iw))
    return tuple(feats)


def fp_distance(a: Tuple, b: Tuple) -> int:
    if not a or not b:
        return 10**9
    n = min(len(a), len(b))
    dist = abs(len(a) - len(b)) * 50
    for i in range(n):
        dist += sum(abs(x - y) for x, y in zip(a[i], b[i]))
    return dist


def train_replay(payload: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
    preds = payload.get("train_predictions")
    if preds is None:
        s4 = payload.get("s4") or {}
        if isinstance(s4, dict):
            typed = s4.get("typed_candidate") or {}
            if isinstance(typed, dict):
                preds = typed.get("train_predictions")
        elif isinstance(payload.get("typed_candidate"), dict):
            preds = payload["typed_candidate"].get("train_predictions")
    if not isinstance(preds, list):
        return {
            "accepted": False,
            "train_replay": f"0/{len(task['train'])}",
            "detail": "missing_train_predictions",
        }
    ok = 0
    for i, ex in enumerate(task["train"]):
        got = parse_grid(preds[i]) if i < len(preds) else None
        if got == ex["output"]:
            ok += 1
    total = len(task["train"])
    perfect = ok == total and total > 0
    return {
        "accepted": perfect,
        "train_replay": f"{ok}/{total}",
        "detail": f"train_replay_{ok}_{total}",
        "passed": ok,
        "total": total,
    }


def extract_test_preds(
    payload: Dict[str, Any], task: Dict[str, Any]
) -> Optional[List[Dict[str, Grid]]]:
    raw = payload.get("test_predictions") or payload.get("test_outputs")
    if raw is None and isinstance(payload.get("typed_candidate"), dict):
        raw = payload["typed_candidate"].get("test_predictions")
    s4 = payload.get("s4")
    if raw is None and isinstance(s4, dict):
        typed = s4.get("typed_candidate")
        if isinstance(typed, dict):
            raw = typed.get("test_predictions")
    if raw is None:
        return None
    if isinstance(raw, dict):
        raw = [raw.get(str(i), raw.get(i)) for i in range(len(task["test"]))]
    if not isinstance(raw, list) or len(raw) < len(task["test"]):
        return None
    out: List[Dict[str, Grid]] = []
    for i, _case in enumerate(task["test"]):
        item = raw[i]
        a1 = a2 = None
        if isinstance(item, dict):
            a1 = parse_grid(
                item.get("attempt_1") or item.get("output") or item.get("grid")
            )
            a2 = parse_grid(
                item.get("attempt_2")
                or item.get("attempt_1")
                or item.get("output")
            )
        else:
            a1 = parse_grid(item)
            a2 = a1
        if a1 is None:
            return None
        if a2 is None:
            a2 = [list(r) for r in a1]
        out.append({"attempt_1": a1, "attempt_2": a2})
    return out


def rank_experiences(
    task: Dict[str, Any],
    experiences: Sequence[Dict[str, Any]],
    eval_challenges: Dict[str, Any],
    limit: int = 10,
) -> List[Dict[str, Any]]:
    tfp = fingerprint(task)
    scored = []
    for ex in experiences:
        eid = str(ex.get("task_id") or "")
        if eid in eval_challenges:
            dist = fp_distance(tfp, fingerprint(eval_challenges[eid]))
        else:
            dist = 10**6
        scored.append((dist, ex))
    scored.sort(key=lambda x: x[0])
    return [ex for _, ex in scored[:limit]]


def solve_one(
    session: requests.Session,
    *,
    base: str,
    key: str,
    model: str,
    tid: str,
    task: Dict[str, Any],
    experiences: List[Dict[str, Any]],
    max_turns: int,
    timeout: int,
) -> Dict[str, Any]:
    train_pack = [
        {
            "i": i,
            "in_shape": [len(ex["input"]), len(ex["input"][0])],
            "out_shape": [len(ex["output"]), len(ex["output"][0])],
            "input": grid_str(ex["input"]),
            "output": grid_str(ex["output"]),
        }
        for i, ex in enumerate(task["train"])
    ]
    test_pack = [
        {
            "i": i,
            "in_shape": [len(case["input"]), len(case["input"][0])],
            "input": grid_str(case["input"]),
        }
        for i, case in enumerate(task["test"])
    ]
    # Compact experience digest for prompt (engines + c4 snippets)
    exp_digest = []
    for ex in experiences[:8]:
        exp_digest.append(
            {
                "task_id": ex.get("task_id"),
                "engine": ex.get("engine"),
                "status": ex.get("status"),
                "c4": str(ex.get("c4_invariant") or "")[:160],
                "grammar_update": str(ex.get("grammar_update") or "")[:120],
                "train_replay": (ex.get("validator_result") or {}).get("train_replay"),
            }
        )

    system = (
        projection_system_prompt(franklin_uum8d_game_comprehension_system_prompt())
        + f"""
Platform ARC-AGI-2 TEST task {tid}. Pull LEARNED_CLOSED_EXPERIENCES before inventing.
Jordan loop: LOCKED only after demonstration_replay zero remainder (all train outputs match).
Reply with ONE JSON object only. Required keys:
  task_id, track, s1, s2, s3, s4, train_predictions, test_predictions,
  grammar_update, closure_ready
train_predictions: list of digit-string grids matching EVERY train output exactly.
test_predictions: list of {{attempt_1, attempt_2}} digit-string grids (attempt_1 ≠ test input).
s4.status is LOCKED only if train_predictions perfect; else REINJECT.
Reuse engines/c4 from learned experiences when they fit the demos.
"""
    )
    evidence = {
        "task_id": tid,
        "track": "arc2",
        "train": train_pack,
        "test": test_pack,
        "LEARNED_CLOSED_EXPERIENCES": exp_digest,
        "platform": "kaggle_test_identity_residue",
    }
    wrapper = build_miss_wrapper_evidence(
        track=TRACK_ARC2,
        task_id=tid,
        s_state="incomplete",
        drift_kind="platform_identity_unlicensed",
        evidence=evidence,
        prior_turns=0,
        learned_experiences=experiences[:10],
    )
    user = exam_s4_user_prompt(wrapper, json.dumps(evidence, sort_keys=True)[:6000])
    # Append explicit train/test pack (exam_s4_user_prompt truncates miss evidence)
    user += (
        "\nAlso include train_predictions and test_predictions keys as specified.\n"
        f"train_demos={json.dumps(train_pack)}\n"
        f"test_inputs={json.dumps(test_pack)}\n"
        f"LEARNED_CLOSED_EXPERIENCES={json.dumps(exp_digest)}\n"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    last_vr: Dict[str, Any] = {"accepted": False}
    for turn in range(max_turns):
        try:
            resp = session.post(
                f"{base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "temperature": 0.15,
                    "max_tokens": 2400,
                    "messages": messages,
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            payload = resp.json()
            msg = payload["choices"][0]["message"]
            answer = str(
                msg.get("content") or msg.get("reasoning_content") or ""
            ).strip()
        except Exception as exc:  # noqa: BLE001
            return {
                "task_id": tid,
                "ok": False,
                "error": str(exc),
                "turns": turn,
                "learned_experiences_pulled": len(experiences),
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
                            "instruction": "ONE JSON object only with train_predictions+test_predictions.",
                        }
                    ),
                }
            )
            continue
        vr = train_replay(parsed, task)
        last_vr = vr
        bound = jordan_loop_bound_closed(TRACK_ARC2, vr, accepted=bool(vr.get("accepted")))
        if bound["closed"]:
            preds = extract_test_preds(parsed, task)
            if preds is None:
                messages.append(
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "gate": "S4_REINJECT",
                                "jordan_loop_bound": bound,
                                "validator_result": vr,
                                "instruction": (
                                    "Train replay CLOSED but test_predictions missing. "
                                    "Emit test_predictions now; keep train_predictions exact."
                                ),
                            }
                        ),
                    }
                )
                continue
            licensed = sum(
                1
                for i, p in enumerate(preds)
                if p["attempt_1"] != task["test"][i]["input"]
            )
            if licensed <= 0:
                return {
                    "task_id": tid,
                    "ok": False,
                    "reason": "identity_after_jordan_closed",
                    "turns": turn + 1,
                    "validator_result": vr,
                    "jordan_loop_bound": bound,
                    "learned_experiences_pulled": len(experiences),
                }
            return {
                "task_id": tid,
                "ok": True,
                "predictions": preds,
                "licensed_grids": licensed,
                "turns": turn + 1,
                "validator_result": vr,
                "jordan_loop_bound": bound,
                "learned_experiences_pulled": len(experiences),
                "experience_task_ids": [e.get("task_id") for e in experiences[:8]],
            }
        messages.append(
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "gate": "S4_REINJECT",
                        "jordan_loop_bound": bound,
                        "validator_result": vr,
                        "instruction": (
                            "Jordan loop OPEN. Revise C4 using LEARNED_CLOSED_EXPERIENCES. "
                            "train_predictions must match demos exactly before LOCKED."
                        ),
                        "LEARNED_CLOSED_EXPERIENCES": exp_digest[:6],
                    }
                ),
            }
        )
    return {
        "task_id": tid,
        "ok": False,
        "turns": max_turns,
        "validator_result": last_vr,
        "jordan_loop_bound": jordan_loop_bound_closed(
            TRACK_ARC2, last_vr, accepted=bool(last_vr.get("accepted"))
        ),
        "learned_experiences_pulled": len(experiences),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--task-ids-file", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, default=None)
    parser.add_argument("--max-turns", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--experience-limit", type=int, default=80)
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    state_dir = (args.state_dir or (root / "reports/exam_reinjection")).resolve()

    base = os.environ.get("FRANKLIN_S4_BASE_URL", "http://127.0.0.1:8080/v1").rstrip("/")
    key = os.environ.get("OPENAI_API_KEY", "uum8d-hle-verifier")
    model = os.environ.get("FRANKLIN_S4_MODEL", "qwen/qwen3.6-35b-a3b")

    challenges = json.loads(
        (root / "data/arc-prize-2026-agi-2/arc-agi_test_challenges.json").read_text()
    )
    eval_ch = json.loads(
        (root / "data/arc-prize-2026-agi-2/arc-agi_evaluation_challenges.json").read_text()
    )
    ids = json.loads(args.task_ids_file.read_text())
    if args.limit > 0:
        ids = ids[: args.limit]

    all_exp = load_learned_experiences(
        state_dir, track=TRACK_ARC2, limit=args.experience_limit
    )
    print(
        f"LOADED closed_experiences={len(all_exp)} state_dir={state_dir}",
        flush=True,
    )

    submission: Dict[str, Any] = {}
    receipts: Dict[str, Any] = {}
    partial = out / "submission.partial.json"
    receipt_path = out / "receipts.partial.json"
    if partial.is_file():
        submission = json.loads(partial.read_text())
        receipts = (
            json.loads(receipt_path.read_text()) if receipt_path.is_file() else {}
        )
        print(f"RESUME done={len(submission)}/{len(ids)}", flush=True)

    session = requests.Session()
    pending = [t for t in ids if t not in submission]
    print(
        f"START franklin_s4_experience pending={len(pending)} model={model}",
        flush=True,
    )
    t0 = time.time()
    for n, tid in enumerate(pending, 1):
        ranked = rank_experiences(
            challenges[tid], all_exp, eval_ch, limit=10
        )
        # Always refresh global pull + ranked for this play
        fresh = load_learned_experiences(
            state_dir, track=TRACK_ARC2, exclude_task_id=tid, limit=args.experience_limit
        )
        ranked = rank_experiences(challenges[tid], fresh, eval_ch, limit=10)
        result = solve_one(
            session,
            base=base,
            key=key,
            model=model,
            tid=tid,
            task=challenges[tid],
            experiences=ranked,
            max_turns=args.max_turns,
            timeout=args.timeout,
        )
        receipts[tid] = {k: v for k, v in result.items() if k != "predictions"}
        if result.get("ok") and result.get("predictions"):
            submission[tid] = result["predictions"]
        partial.write_text(
            json.dumps(submission, separators=(",", ":")), encoding="utf-8"
        )
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
            f"bound={(result.get('jordan_loop_bound') or {}).get('closed')} "
            f"exp_pulled={result.get('learned_experiences_pulled')} "
            f"elapsed={time.time()-t0:.0f}s tid={tid}",
            flush=True,
        )

    (out / "submission.json").write_text(
        json.dumps(submission, separators=(",", ":")), encoding="utf-8"
    )
    print(
        f"DONE experience_s4 stored={len(submission)} → {out / 'submission.json'}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
