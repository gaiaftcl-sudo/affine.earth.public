"""Offline checks for open-AGI / hardest-exam scaffolding.

Never contacts live endpoints. Never invents scores.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OPEN_AGI_YAML = ROOT / "configs" / "open-agi-harnesses.yaml"
THIRD_PARTY_YAML = ROOT / "configs" / "third-party-harnesses.yaml"
LAUNCHER = ROOT / "bin" / "run-open-agi-harnesses.sh"
OPEN_AGI_DOC = ROOT / "docs" / "OPEN_AGI_FRAMEWORKS.md"


def _parse_simple_yaml_keys(text: str) -> set[str]:
    """Collect indented keys under suites:/harnesses: without PyYAML."""
    keys: set[str] = set()
    section = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if line in ("suites:", "harnesses:"):
            section = line[:-1]
            continue
        if section and line.startswith("  ") and not line.startswith("   "):
            stripped = line.strip()
            if stripped.endswith(":") and not stripped.startswith("#"):
                keys.add(stripped[:-1])
        if line and not line.startswith(" ") and line.endswith(":") and line[:-1] not in (
            "suites",
            "harnesses",
        ):
            if section and line.split(":")[0] not in ("suites", "harnesses"):
                section = None
    return keys


def test_open_agi_registry_files_exist():
    assert OPEN_AGI_YAML.is_file()
    assert THIRD_PARTY_YAML.is_file()
    assert LAUNCHER.is_file()
    assert os.access(LAUNCHER, os.X_OK)
    assert OPEN_AGI_DOC.is_file()


def test_open_agi_suite_ids_present():
    text = OPEN_AGI_YAML.read_text(encoding="utf-8")
    for suite_id in (
        "open_agi_hle",
        "open_agi_arc_agi",
        "open_agi_arc_agi_2",
        "open_agi_gpqa",
        "open_agi_bbh",
        "open_agi_mmlu_pro",
        "open_agi_lm_eval_hard",
        "open_agi_gaia",
        "open_agi_inspect_gpqa",
        "open_agi_swe_bench",
        "open_agi_livecodebench",
        "open_agi_frontiermath",
    ):
        assert f"{suite_id}:" in text
    keys = _parse_simple_yaml_keys(text)
    assert "open_agi_hle" in keys
    assert "hle" in keys
    assert "gpqa" in keys
    assert "livecodebench" in keys
    assert "frontiermath" in keys


def test_third_party_yaml_cross_links_open_agi():
    text = THIRD_PARTY_YAML.read_text(encoding="utf-8")
    assert "open_agi_registry: configs/open-agi-harnesses.yaml" in text
    assert "open_agi_gpqa_via_lm_eval:" in text
    assert "open_agi_arc_agi_2:" in text
    assert "open_agi_frontiermath:" in text


def test_open_agi_doc_links_registry_and_launcher():
    text = OPEN_AGI_DOC.read_text(encoding="utf-8")
    assert "configs/open-agi-harnesses.yaml" in text
    assert "bin/run-open-agi-harnesses.sh" in text
    assert "NEEDS_UPSTREAM" in text
    assert "cais/hle" in text
    assert "arc-agi-2" in text
    assert "livecodebench" in text


def test_launcher_help_exits_zero():
    proc = subprocess.run(
        [str(LAUNCHER), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "gpqa" in proc.stdout
    assert "arc-agi-2" in proc.stdout
    assert "livecodebench" in proc.stdout
    assert "frontiermath" in proc.stdout


def test_launcher_requires_harness_selection():
    proc = subprocess.run(
        [str(LAUNCHER)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "AFFINE_HARNESS_ENV_FILE": ""},
    )
    assert proc.returncode == 2
    assert "select at least one harness" in proc.stderr


def test_frontiermath_fails_loudly_needs_upstream():
    env = {
        **os.environ,
        "AFFINE_HARNESS_ENV_FILE": str(ROOT / "configs" / "third-party-harnesses.env.example"),
    }
    proc = subprocess.run(
        [str(LAUNCHER), "--harness", "frontiermath"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert proc.returncode == 3
    assert "NEEDS_UPSTREAM" in proc.stderr
    assert "frontiermath" in proc.stderr.lower() or "FrontierMath" in proc.stderr
    assert "invent" in proc.stderr.lower() or "heredoc" in proc.stderr.lower()


def test_swe_bench_fails_loudly_without_predictions():
    env = {
        **os.environ,
        "AFFINE_HARNESS_ENV_FILE": str(ROOT / "configs" / "third-party-harnesses.env.example"),
    }
    env.pop("SWE_BENCH_PREDICTIONS_PATH", None)
    # Ensure example env does not define predictions
    proc = subprocess.run(
        [str(LAUNCHER), "--harness", "swe-bench"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    # 127 if swebench missing, 2 if installed but predictions missing
    assert proc.returncode in (2, 127)
    assert "FATAL" in proc.stderr
    assert "invent" in proc.stderr.lower() or "predictions" in proc.stderr.lower() or "swebench" in proc.stderr.lower()


def test_livecodebench_fails_loudly_without_checkout():
    env = {
        **os.environ,
        "AFFINE_HARNESS_ENV_FILE": str(ROOT / "configs" / "third-party-harnesses.env.example"),
        "LCB_HARNESS_DIR": str(ROOT / "harnesses" / "_missing_LiveCodeBench"),
    }
    proc = subprocess.run(
        [str(LAUNCHER), "--harness", "livecodebench"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert proc.returncode == 2
    assert "FATAL" in proc.stderr
    assert "LiveCodeBench" in proc.stderr or "checkout" in proc.stderr.lower()


def test_arc_agi_2_fails_loudly_without_data():
    env = {
        **os.environ,
        "AFFINE_HARNESS_ENV_FILE": str(ROOT / "configs" / "third-party-harnesses.env.example"),
        "ARC_AGI_2_DIR": str(ROOT / "harnesses" / "_missing_ARC-AGI-2"),
        "ARC_AGI_CONFIG": "dummy-config",
    }
    proc = subprocess.run(
        [str(LAUNCHER), "--harness", "arc-agi-2"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert proc.returncode == 2
    assert "FATAL" in proc.stderr


def test_gpqa_fails_loudly_without_lm_eval():
    """If lm_eval is missing, exit 127 — never write fake GPQA scores."""
    env = {
        **os.environ,
        "AFFINE_HARNESS_ENV_FILE": str(ROOT / "configs" / "third-party-harnesses.env.example"),
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    }
    which = subprocess.run(["bash", "-lc", "command -v lm_eval || true"], capture_output=True, text=True)
    if which.stdout.strip():
        pytest.skip("lm_eval present on default PATH; skip missing-CLI assertion")
    proc = subprocess.run(
        [str(LAUNCHER), "--harness", "gpqa"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert proc.returncode in (2, 127)
    assert "FATAL" in proc.stderr
    assert "heredoc" not in proc.stdout.lower()
