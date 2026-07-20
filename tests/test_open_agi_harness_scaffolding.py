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
            # top-level key under section: "  open_agi_hle:"
            stripped = line.strip()
            if stripped.endswith(":") and not stripped.startswith("#"):
                keys.add(stripped[:-1])
        if line and not line.startswith(" ") and line.endswith(":") and line[:-1] not in (
            "suites",
            "harnesses",
        ):
            # left a nested block at indent 0
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
        "open_agi_gpqa",
        "open_agi_gaia",
        "open_agi_swe_bench",
        "open_agi_livecodebench",
    ):
        assert f"{suite_id}:" in text
    keys = _parse_simple_yaml_keys(text)
    assert "open_agi_hle" in keys
    assert "hle" in keys
    assert "gpqa" in keys


def test_third_party_yaml_cross_links_open_agi():
    text = THIRD_PARTY_YAML.read_text(encoding="utf-8")
    assert "open_agi_registry: configs/open-agi-harnesses.yaml" in text
    assert "open_agi_gpqa_via_lm_eval:" in text


def test_open_agi_doc_links_registry_and_launcher():
    text = OPEN_AGI_DOC.read_text(encoding="utf-8")
    assert "configs/open-agi-harnesses.yaml" in text
    assert "bin/run-open-agi-harnesses.sh" in text
    assert "NEEDS_UPSTREAM" in text
    assert "cais/hle" in text


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
    assert "NEEDS_UPSTREAM" in proc.stdout or "NEEDS_UPSTREAM" in proc.stderr or "swe-bench" in proc.stdout


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


def test_swe_bench_fails_loudly_needs_upstream():
    # Clear endpoint env so we prove NEEDS_UPSTREAM fires before inventing scores.
    env = {
        k: v
        for k, v in os.environ.items()
        if k
        not in (
            "AFFINE_HARNESS_ENDPOINT",
            "AFFINE_OPENAI_BASE_URL",
            "OPENAI_BASE_URL",
            "AFFINE_BASE_URL",
            "OPENAI_API_KEY",
            "AFFINE_HARNESS_API_KEY",
        )
    }
    # Avoid auto-sourcing a local .env if present
    env["AFFINE_HARNESS_ENV_FILE"] = str(ROOT / "configs" / "third-party-harnesses.env.example")
    # env.example has placeholder endpoint — swe-bench must still exit 3 without calling APIs
    proc = subprocess.run(
        [str(LAUNCHER), "--harness", "swe-bench"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert proc.returncode == 3
    assert "NEEDS_UPSTREAM" in proc.stderr
    assert "SWE-bench" in proc.stderr
    assert "heredoc" in proc.stderr.lower() or "invent" in proc.stderr.lower()


def test_livecodebench_fails_loudly_needs_upstream():
    env = {**os.environ, "AFFINE_HARNESS_ENV_FILE": str(ROOT / "configs" / "third-party-harnesses.env.example")}
    proc = subprocess.run(
        [str(LAUNCHER), "--harness", "livecodebench"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert proc.returncode == 3
    assert "NEEDS_UPSTREAM" in proc.stderr
    assert "LiveCodeBench" in proc.stderr


def test_gpqa_fails_loudly_without_lm_eval():
    """If lm_eval is missing, exit 127 — never write fake GPQA scores."""
    env = {
        **os.environ,
        "AFFINE_HARNESS_ENV_FILE": str(ROOT / "configs" / "third-party-harnesses.env.example"),
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    }
    # Ensure lm_eval not on PATH even if installed elsewhere
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
    # Either missing lm_eval (127) or missing/invalid endpoint after finding lm_eval
    assert proc.returncode in (2, 127)
    assert "FATAL" in proc.stderr
    assert "heredoc" not in proc.stdout.lower()
