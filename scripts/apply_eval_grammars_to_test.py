#!/usr/bin/env python3
"""Apply sealed labeled-eval grammar solvers to AGI-2 Kaggle test tasks.

For each IDENTITY platform grid/task, try CLOSED grammar engines (and other
arc/*.py modules exposing train_replay + submission_fragment). Accept only
train-replay-perfect non-identity fills. No Kaggle submit. No private labels.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _discover_engines(root: Path) -> List[Tuple[str, str]]:
    """Return list of (engine_name, module_path)."""
    arc = root / "llm_llvm_bench/arc"
    engines: Dict[str, Path] = {}
    # From CLOSED grammars
    grammar_dir = root / "reports/exam_reinjection/grammar/arc2"
    if grammar_dir.is_dir():
        for gp in grammar_dir.glob("*.json"):
            try:
                g = json.loads(gp.read_text(encoding="utf-8"))
            except Exception:
                continue
            closed = g.get("status") == "CLOSED" or g.get("last_gate") == "LOCKED"
            if not closed:
                continue
            eng = g.get("engine")
            if not eng or eng == "?":
                continue
            candidate = arc / f"{eng}.py"
            if candidate.is_file():
                engines[eng] = candidate
    # All s1_/s2_/s3_/marker/container modules with API
    for path in sorted(arc.glob("*.py")):
        name = path.stem
        if name.startswith("_") or name in (
            "local_hybrid_solver",
            "icecuber_adapter",
            "franklin_s4_projection",
            "franklin_uum8d_system_prompt",
            "agi3_platformer_policy",
        ):
            continue
        if name.startswith(("s1_", "s2_", "s3_", "marker", "container", "eight_")):
            engines.setdefault(name, path)
    return sorted((n, str(p)) for n, p in engines.items())


def _try_task(payload: Tuple[str, str, Dict[str, Any], List[Tuple[str, str]]]) -> Dict[str, Any]:
    root_s, tid, task, engine_list = payload
    root = Path(root_s)
    best = None
    best_eng = None
    tried = 0
    for eng, path_s in engine_list:
        path = Path(path_s)
        tried += 1
        try:
            mod = _load_module(path, f"gram_{eng}")
            if not hasattr(mod, "train_replay") or not hasattr(mod, "submission_fragment"):
                continue
            if hasattr(mod, "applies"):
                try:
                    if not mod.applies(task):
                        continue
                except Exception:
                    pass
            replay = mod.train_replay(task)
            if not (isinstance(replay, dict) and replay.get("perfect")):
                continue
            frag = mod.submission_fragment(tid, task)
            if not frag or tid not in frag:
                continue
            preds = frag[tid]
            if len(preds) != len(task["test"]):
                continue
            # require non-identity attempt_1 on at least one test
            non_id = 0
            ok_shape = True
            for i, case in enumerate(task["test"]):
                a1 = preds[i].get("attempt_1")
                a2 = preds[i].get("attempt_2")
                if not isinstance(a1, list) or not isinstance(a2, list):
                    ok_shape = False
                    break
                if a1 != case["input"]:
                    non_id += 1
            if not ok_shape or non_id == 0:
                continue
            best = preds
            best_eng = eng
            break  # first sealed licensed win
        except Exception:
            continue
    return {
        "task_id": tid,
        "predictions": best,
        "engine": best_eng,
        "engines_tried": tried,
        "licensed_grids": (
            sum(
                1
                for i, case in enumerate(task["test"])
                if best is not None and best[i]["attempt_1"] != case["input"]
            )
            if best
            else 0
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--base-submission",
        type=Path,
        default=None,
        help="Starting submission (default: merged airgap canonical)",
    )
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    root = args.root.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    challenges = json.loads(
        (root / "data/arc-prize-2026-agi-2/arc-agi_test_challenges.json").read_text(
            encoding="utf-8"
        )
    )
    base_path = args.base_submission or (
        root / "reports/airgap_agi2_test_20260721T175400Z/submission.json"
    )
    submission = json.loads(base_path.read_text(encoding="utf-8"))

    identity_tasks = []
    for tid in sorted(challenges):
        preds = submission.get(tid)
        if not preds:
            identity_tasks.append(tid)
            continue
        if any(
            preds[i]["attempt_1"] == challenges[tid]["test"][i]["input"]
            for i in range(len(preds))
        ):
            # any identity grid → retry whole task
            if all(
                preds[i]["attempt_1"] == challenges[tid]["test"][i]["input"]
                for i in range(len(preds))
            ):
                identity_tasks.append(tid)

    engines = _discover_engines(root)
    print(
        f"identity_tasks={len(identity_tasks)} engines={len(engines)} "
        f"workers={args.workers}",
        flush=True,
    )

    lifts = []
    t0 = time.time()
    payloads = [
        (str(root), tid, challenges[tid], engines) for tid in identity_tasks
    ]
    done = 0
    with ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futs = {pool.submit(_try_task, p): p[1] for p in payloads}
        for fut in as_completed(futs):
            res = fut.result()
            done += 1
            if res["predictions"] is not None:
                submission[res["task_id"]] = res["predictions"]
                lifts.append(
                    {
                        "task_id": res["task_id"],
                        "engine": res["engine"],
                        "licensed_grids": res["licensed_grids"],
                    }
                )
                print(
                    f"LIFT {res['task_id']} engine={res['engine']} "
                    f"grids={res['licensed_grids']}",
                    flush=True,
                )
            if done % 20 == 0 or done == len(payloads):
                print(
                    f"progress {done}/{len(payloads)} lifts={len(lifts)} "
                    f"elapsed={time.time()-t0:.1f}s",
                    flush=True,
                )

    out_sub = out_dir / "submission.json"
    out_sub.write_text(json.dumps(submission, separators=(",", ":")), encoding="utf-8")

    lic = ident = 0
    for tid, preds in submission.items():
        for i, pred in enumerate(preds):
            if pred["attempt_1"] != challenges[tid]["test"][i]["input"]:
                lic += 1
            else:
                ident += 1
    receipt = {
        "kind": "agi2_eval_grammar_apply_to_test",
        "base": str(base_path.relative_to(root)),
        "identity_tasks_input": len(identity_tasks),
        "lifts": lifts,
        "lift_tasks": len(lifts),
        "licensed_grids": lic,
        "identity_grids": ident,
        "licensed_pct": round(100.0 * lic / max(1, lic + ident), 2),
        "engines": len(engines),
        "elapsed_s": time.time() - t0,
    }
    (out_dir / "GRAMMAR_APPLY_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"DONE licensed={lic}/259 identity={ident} lifts={len(lifts)} → {out_sub}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
