"""Live Affine.Earth signup-surface smoke (opt-in; no fake users).

Skipped unless AFFINE_LIVE_SMOKE=1 so default pytest stays offline-safe.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_affine_signup_surface.py"

pytestmark = pytest.mark.skipif(
    os.environ.get("AFFINE_LIVE_SMOKE", "").strip() not in {"1", "true", "yes"},
    reason="Set AFFINE_LIVE_SMOKE=1 to probe live Affine.Earth signup UI",
)


def test_signup_surface_script_exits_zero():
    assert SCRIPT.is_file()
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
    assert "SIGNUP_SURFACE_REACHABLE" in proc.stdout
    assert '"ok": true' in proc.stdout
    # Must not claim registration success.
    assert "account created" not in proc.stdout.lower()
    assert "registration success" not in proc.stdout.lower()
