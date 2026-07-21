"""Thin offline adapter around the MIT-licensed ARC-icecuber CPU solver.

Vendored tree: harnesses/arc-icecuber (see THIRD_PARTY.md).
Never submits to Kaggle. Predictions are exact-match scored locally only.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

Grid = List[List[int]]

ROOT_MARKERS = ("harnesses", "arc-icecuber")


def default_solver_root(repo_root: Path) -> Path:
    return repo_root / "harnesses" / "arc-icecuber"


def ensure_built(solver_root: Path) -> Path:
    binary = solver_root / "run"
    if binary.is_file() and os.access(binary, os.X_OK):
        return binary
    completed = subprocess.run(
        ["make", "-j"],
        cwd=str(solver_root),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0 or not binary.is_file():
        raise RuntimeError(
            "arc-icecuber build failed:\n"
            + (completed.stdout or "")
            + "\n"
            + (completed.stderr or "")
        )
    return binary


def _write_task_dir(
    challenges: Dict[str, Any],
    solutions: Optional[Dict[str, Any]],
    target: Path,
) -> List[Tuple[str, int]]:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    sample_ids: List[Tuple[str, int]] = []
    for task_id in sorted(challenges):
        task = json.loads(json.dumps(challenges[task_id]))
        if solutions is not None and task_id in solutions:
            for index, case in enumerate(task["test"]):
                case["output"] = solutions[task_id][index]
        (target / f"{task_id}.json").write_text(json.dumps(task), encoding="utf-8")
        for index in range(len(task["test"])):
            sample_ids.append((task_id, index))
    return sample_ids


_PIPE_ROW = re.compile(r"\|([0-9|]+)\|")


def parse_answer_csv(path: Path) -> List[Tuple[Grid, float]]:
    """Parse icecuber writeAnswersWithScores output into (grid, score) pairs."""
    if not path.is_file():
        return []
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return []
    answers: List[Tuple[Grid, float]] = []
    for line in lines[1:]:
        # Format: |row|row|...| <score>
        if "|" not in line:
            continue
        score = 0.0
        body = line
        if " " in line.rsplit("|", 1)[-1] or line.split()[-1].replace(".", "", 1).isdigit():
            parts = line.rsplit(None, 1)
            if len(parts) == 2:
                try:
                    score = float(parts[1])
                    body = parts[0]
                except ValueError:
                    pass
        rows = [chunk for chunk in body.split("|") if chunk != ""]
        if not rows:
            continue
        grid = [[int(ch) for ch in row] for row in rows]
        answers.append((grid, score))
    return answers


def _run_one(
    binary: Path,
    sample_dir: Path,
    sample_index: int,
    depth: int,
    output_dir: Path,
    work_dir: Path,
) -> Tuple[int, str, List[Tuple[Grid, float]]]:
    log_path = work_dir / f"log_{sample_index}.txt"
    # icecuber writes to cwd/output/answer_{sid}_{depth}.csv
    env = os.environ.copy()
    # Bound per-sample wall time so hybrid licensed-fill can advance.
    # Unset / 0 = unlimited (legacy). Default 45s keeps private-test sweeps moving.
    timeout_raw = env.get("ARC_ICECUBER_TIMEOUT_S", "45").strip()
    timeout_s: Optional[float]
    try:
        timeout_s = float(timeout_raw) if timeout_raw not in ("", "0") else None
    except ValueError:
        timeout_s = 45.0
    try:
        completed = subprocess.run(
            [str(binary), str(sample_dir), str(sample_index), str(depth)],
            cwd=str(work_dir),
            text=True,
            capture_output=True,
            check=False,
            env=env,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        log_path.write_text(
            f"TIMEOUT after {timeout_s}s\n{(exc.stdout or '')}\n{(exc.stderr or '')}",
            encoding="utf-8",
        )
        return sample_index, "Nothing", []
    log_path.write_text(
        (completed.stdout or "") + "\n" + (completed.stderr or ""), encoding="utf-8"
    )
    text = log_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(
        r"Task #\s*\d+ \(([^)]+)\):\s*.*?(Correct|Candidate|Dimensions|Nothing)",
        text,
    )
    verdict = match.group(2) if match else "PARSE_FAIL"
    answer_path = work_dir / "output" / f"answer_{sample_index}_{depth}.csv"
    # Also accept solver_root-relative output if binary was invoked differently.
    if not answer_path.is_file():
        answer_path = output_dir / f"answer_{sample_index}_{depth}.csv"
    return sample_index, verdict, parse_answer_csv(answer_path)


def solve_challenge_set(
    repo_root: Path,
    challenges: Dict[str, Any],
    solutions: Optional[Dict[str, Any]] = None,
    *,
    depth: int = 2,
    workers: int = 6,
    solver_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run icecuber on a challenge dict; return predictions + verdict stats."""
    solver_root = solver_root or default_solver_root(repo_root)
    binary = ensure_built(solver_root)
    with tempfile.TemporaryDirectory(prefix="arc_icecuber_") as tmp:
        tmp_path = Path(tmp)
        sample_dir = tmp_path / "samples"
        sample_ids = _write_task_dir(challenges, solutions, sample_dir)
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        (work_dir / "output").mkdir()
        # symlink dataset placeholder unused; absolute sample_dir is enough
        # Copy binary into work so relative output paths stay local to the job.
        local_bin = work_dir / "run"
        shutil.copy2(binary, local_bin)
        local_bin.chmod(0o755)

        predictions: Dict[str, List[Dict[str, Grid]]] = {
            task_id: [
                {
                    "attempt_1": [list(row) for row in case["input"]],
                    "attempt_2": [list(row) for row in case["input"]],
                }
                for case in challenges[task_id]["test"]
            ]
            for task_id in challenges
        }
        verdicts: Dict[str, int] = {
            "Correct": 0,
            "Candidate": 0,
            "Dimensions": 0,
            "Nothing": 0,
            "PARSE_FAIL": 0,
        }
        exact_grids = 0
        total_grids = len(sample_ids)

        def job(index: int) -> Tuple[int, str, List[Tuple[Grid, float]]]:
            # Each worker needs isolated cwd/output to avoid clobbering.
            worker_dir = work_dir / f"w{index}"
            worker_dir.mkdir(exist_ok=True)
            (worker_dir / "output").mkdir(exist_ok=True)
            worker_bin = worker_dir / "run"
            if not worker_bin.exists():
                shutil.copy2(local_bin, worker_bin)
                worker_bin.chmod(0o755)
            return _run_one(
                worker_bin, sample_dir, index, depth, worker_dir / "output", worker_dir
            )

        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            futures = [pool.submit(job, i) for i in range(len(sample_ids))]
            for future in as_completed(futures):
                index, verdict, answers = future.result()
                task_id, test_index = sample_ids[index]
                verdicts[verdict] = verdicts.get(verdict, 0) + 1
                if answers:
                    attempt_1 = answers[0][0]
                    attempt_2 = answers[1][0] if len(answers) > 1 else attempt_1
                    predictions[task_id][test_index] = {
                        "attempt_1": attempt_1,
                        "attempt_2": attempt_2,
                    }
                    if solutions is not None and task_id in solutions:
                        expected = solutions[task_id][test_index]
                        if attempt_1 == expected or attempt_2 == expected:
                            exact_grids += 1

        return {
            "engine": "arc-icecuber",
            "license": "MIT",
            "depth": depth,
            "workers": workers,
            "sample_count": total_grids,
            "exact_grids": exact_grids,
            "exact_rate": (exact_grids / total_grids) if total_grids else 0.0,
            "verdicts": verdicts,
            "predictions": predictions,
            "sample_ids": sample_ids,
        }


def predictions_for_task(
    repo_root: Path,
    task_id: str,
    task: Dict[str, Any],
    *,
    depth: int = 2,
    solver_root: Optional[Path] = None,
) -> List[Dict[str, Grid]]:
    """Solve a single task; return attempt pairs for each test input."""
    result = solve_challenge_set(
        repo_root,
        {task_id: task},
        None,
        depth=depth,
        workers=1,
        solver_root=solver_root,
    )
    return result["predictions"][task_id]
