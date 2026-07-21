#!/usr/bin/env python3
"""Run and record a bounded live Franklin S¹–S⁴ language game."""
from __future__ import annotations
import argparse, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from llm_llvm_bench.arc.franklin_s4_projection import projection_system_prompt, wrapper_evidence
from llm_llvm_bench.arc.franklin_uum8d_system_prompt import franklin_uum8d_game_comprehension_system_prompt

QUESTIONS = (
    "Why might projections not be visible yet? Define measurable S1–S4 for ARC-AGI-2, ARC-AGI-3, and HLE.",
    "For ARC-AGI-2 and ARC-AGI-3, map S1–S4 to input evidence, candidates, a legal discriminator, and typed output.",
    "For HLE, map S1–S4 to the complete record, answer candidates, citation/format checks, and the CAIS artifact.",
    "Specify an implementable wrapper loop: evidence proposal, C4 candidate, validator, and miss reinjection.",
)

def first(*names: str, default: str | None = None) -> str | None:
    return next((os.environ[n] for n in names if os.environ.get(n)), default)

def content(payload: dict[str, Any]) -> str:
    message = payload["choices"][0]["message"]
    return str(message.get("content") or message.get("reasoning_content") or "").strip()

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--max-turns", type=int, default=8)
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    if not 1 <= args.max_turns <= 29:
        raise SystemExit("--max-turns must be 1–29.")
    base = first("FRANKLIN_S4_BASE_URL", "HLE_LOCAL_BASE_URL", "OPENAI_BASE_URL",
                 "AFFINE_HARNESS_ENDPOINT", default="http://127.0.0.1:8080/v1").rstrip("/")
    key = first("OPENAI_API_KEY", "AFFINE_HARNESS_API_KEY", default="uum8d-hle-verifier")
    session = requests.Session()
    models = session.get(f"{base}/models", headers={"Authorization": f"Bearer {key}"}, timeout=15)
    models.raise_for_status()
    model_ids = [x.get("id") for x in models.json().get("data", [])]
    model = first("FRANKLIN_S4_MODEL", "HLE_LOCAL_MODEL", "OPENAI_MODEL", "AFFINE_HARNESS_MODEL")
    model = model or next((x for x in model_ids if x and "embed" not in x), None)
    if not model: raise SystemExit("No chat model returned by endpoint.")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = (args.output_dir or ROOT / "reports" / f"franklin_s4_language_game_{stamp}").resolve()
    out.mkdir(parents=True, exist_ok=False)
    transcript = out / "transcript.jsonl"
    messages = [{"role": "system", "content": projection_system_prompt(
        franklin_uum8d_game_comprehension_system_prompt()) +
        "\nRespond in under 250 words; give concrete evidence fields or compact JSON."}]
    turns: list[dict[str, Any]] = []
    def record(turn: dict[str, Any]) -> None:
        turns.append(turn); transcript.parent.mkdir(parents=True, exist_ok=True)
        with transcript.open("a", encoding="utf-8") as f: f.write(json.dumps(turn, sort_keys=True) + "\n")
    for question in QUESTIONS:
        for kind, prompt in (("QUESTION", question), ("WRAPPER_EVIDENCE", json.dumps(wrapper_evidence(
            track="cross-track", item_id="s4-protocol-dialogue", answer_contract="protocol_json",
            s1={"source": "dialogue", "complete": False},
            s2={"remaining_candidates": ["lock", "reinject"]},
            s3={"next_check": "named validator"},
            prior_gate={"result": "NOT_EVALUATED"}), sort_keys=True))):
            if len(turns) >= args.max_turns: break
            record({"turn_index": len(turns), "actor_role": "wrapper", "turn_kind": kind, "content": prompt})
            messages.append({"role": "user", "content": prompt}); started = time.perf_counter()
            response = session.post(f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": model, "temperature": 0, "max_tokens": args.max_tokens, "messages": messages},
                timeout=args.timeout); response.raise_for_status(); payload = response.json(); answer = content(payload)
            record({"turn_index": len(turns), "actor_role": "franklin",
                    "turn_kind": "S4_PROTOCOL" if kind == "WRAPPER_EVIDENCE" else "ANALYSIS",
                    "content": answer, "finish_reason": payload["choices"][0].get("finish_reason"),
                    "usage": payload.get("usage", {}), "elapsed_ms": round((time.perf_counter()-started)*1000, 2)})
            messages.append({"role": "assistant", "content": answer})
        if len(turns) >= args.max_turns: break
    summary = {"kind": "live_franklin_s4_projection_language_game",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(), "endpoint": base, "model": model,
        "endpoint_models": model_ids, "turn_count": len(turns), "turn_limit": args.max_turns,
        "transcript": str(transcript.relative_to(ROOT)), "official_benchmark_score": None,
        "notes": ["Live model dialogue/protocol capture, not an ARC or HLE evaluation.",
                  "LOCKED requires the named task-native validator."]}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2)); return 0
if __name__ == "__main__": raise SystemExit(main())
