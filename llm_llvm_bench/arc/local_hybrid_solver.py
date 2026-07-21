"""Local hybrid ARC solver: 8-marker readout + replay-gated DSL + icecuber.

FoT path label: LOCAL_HYBRID_SOLVER. Never emits [[0]] placeholders or
unvalidated guesses. Train-replay must pass before attempts are accepted.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

Grid = List[List[int]]


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _is_placeholder(grid: Any) -> bool:
    return grid == [[0]] or grid == [[]]


def _valid_grid(grid: Any) -> bool:
    if not isinstance(grid, list) or not grid or len(grid) > 30:
        return False
    width = None
    for row in grid:
        if not isinstance(row, list) or not row or len(row) > 30:
            return False
        if width is None:
            width = len(row)
        elif len(row) != width:
            return False
        for cell in row:
            if type(cell) is not int or cell < 0 or cell > 9:
                return False
    return not _is_placeholder(grid)


def _dsl_train_replay(solver: Any, train: List[Dict[str, Any]]) -> Dict[str, Any]:
    exact = solver.exact_candidates(train)
    if not exact:
        return {
            "engine": "replay_gated_dsl",
            "ok": False,
            "train_replay": f"0/{len(train)}",
            "train_replay_pass": 0,
            "train_replay_total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    failures = [
        i for i, ex in enumerate(train) if transform(ex["input"]) != ex["output"]
    ]
    passes = len(train) - len(failures)
    return {
        "engine": "replay_gated_dsl",
        "ok": not failures and bool(exact),
        "train_replay": f"{passes}/{len(train)}",
        "train_replay_pass": passes,
        "train_replay_total": len(train),
        "licensed_transforms": [n for n, _ in exact],
        "primary_transform": name,
        "failed_demo_indices": failures,
    }


def _icecuber_train_replay(
    adapter: Any, repo_root: Path, task_id: str, task: Dict[str, Any]
) -> Tuple[Optional[List[Dict[str, Grid]]], Dict[str, Any]]:
    """Icecuber only when every training demonstration is exact-matched."""
    train = task["train"]
    if not train:
        return None, {"engine": "arc-icecuber", "ok": False, "train_replay": "0/0"}
    pseudo = {
        task_id: {
            "train": train,
            "test": [{"input": ex["input"]} for ex in train],
        }
    }
    solutions = {task_id: [ex["output"] for ex in train]}
    try:
        result = adapter.solve_challenge_set(
            repo_root, pseudo, solutions, depth=2, workers=1
        )
    except Exception as exc:
        return None, {
            "engine": "arc-icecuber",
            "ok": False,
            "train_replay": f"0/{len(train)}",
            "error": str(exc),
        }
    preds = result["predictions"][task_id]
    hits = 0
    for index, expected in enumerate(solutions[task_id]):
        pair = preds[index]
        if pair.get("attempt_1") == expected or pair.get("attempt_2") == expected:
            hits += 1
    meta = {
        "engine": "arc-icecuber",
        "ok": hits == len(train),
        "train_replay": f"{hits}/{len(train)}",
        "train_replay_pass": hits,
        "train_replay_total": len(train),
        "verdicts": result.get("verdicts"),
    }
    if hits != len(train):
        return None, meta
    real = adapter.predictions_for_task(repo_root, task_id, task, depth=2)
    return real, meta


def solve_task(
    repo_root: Path, task_id: str, task: Dict[str, Any]
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """Return ({task_id: [attempts...]}, receipt) or (None, receipt) if unlicensed."""
    arc_dir = Path(__file__).resolve().parent
    receipt: Dict[str, Any] = {
        "task_id": task_id,
        "path_label": "LOCAL_HYBRID_SOLVER",
        "engines_tried": [],
        "accepted_engine": None,
        "train_replay": None,
        "ok": False,
    }

    # 1) 8-marker twin-S readout (0934a4d8; icecuber fails train-replay here).
    twin = _load_module(arc_dir / "marker8_twin31.py", "marker8_twin31")
    twin_replay = twin.train_replay(task)
    twin_fragment = twin.submission_fragment(task_id, task)
    receipt["engines_tried"].append(twin_replay)
    if (
        twin_fragment is not None
        and twin_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in twin_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "marker8_twin31"
        receipt["train_replay"] = twin_replay["train_replay"]
        receipt["ok"] = True
        receipt["marker_meta"] = twin_replay
        return twin_fragment, receipt

    marker = _load_module(arc_dir / "eight_marker_extractor.py", "eight_marker_extractor")
    marker_attempts, marker_meta = marker.predictions_for_task(task)
    receipt["engines_tried"].append(marker_meta)
    if marker_attempts is not None and all(
        _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
        for p in marker_attempts
    ):
        receipt["accepted_engine"] = marker_meta["engine"]
        receipt["train_replay"] = marker_meta["train_replay"]
        receipt["ok"] = True
        receipt["marker_meta"] = marker_meta
        return {task_id: marker_attempts}, receipt

    # 2) Replay-gated DSL (db71c28 lineage).
    dsl_path = repo_root / "kaggle/arc-prize-2026-agi-2/arc_agi_2_kaggle.py"
    try:
        dsl = _load_module(dsl_path, "arc_agi_2_dsl_local")
        dsl_meta = _dsl_train_replay(dsl, task["train"])
        receipt["engines_tried"].append(dsl_meta)
        if dsl_meta["ok"]:
            attempts = [dsl.predictions(task, case["input"]) for case in task["test"]]
            if all(
                _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
                for p in attempts
            ):
                receipt["accepted_engine"] = "replay_gated_dsl"
                receipt["train_replay"] = dsl_meta["train_replay"]
                receipt["ok"] = True
                return {task_id: attempts}, receipt
    except Exception as exc:
        receipt["engines_tried"].append(
            {"engine": "replay_gated_dsl", "ok": False, "error": str(exc)}
        )

    # 3) Icecuber only with full train-replay license.
    ice_path = arc_dir / "icecuber_adapter.py"
    try:
        ice = _load_module(ice_path, "arc_icecuber_adapter_local")
        ice_attempts, ice_meta = _icecuber_train_replay(ice, repo_root, task_id, task)
        receipt["engines_tried"].append(ice_meta)
        if ice_attempts is not None and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in ice_attempts
        ):
            receipt["accepted_engine"] = "arc-icecuber"
            receipt["train_replay"] = ice_meta["train_replay"]
            receipt["ok"] = True
            return {task_id: ice_attempts}, receipt
    except Exception as exc:
        receipt["engines_tried"].append(
            {"engine": "arc-icecuber", "ok": False, "error": str(exc)}
        )

    receipt["error"] = "no engine achieved full train-replay; refusing unvalidated guess"
    return None, receipt


def fragment_json(fragment: Dict[str, Any]) -> str:
    return json.dumps(fragment, separators=(",", ":"), sort_keys=True)
