"""Live Affine.Earth signup-surface smoke (opt-in; no fake users).

Skipped unless AFFINE_LIVE_SMOKE=1 so default pytest stays offline-safe.
"""

from __future__ import annotations

import json
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
        [sys.executable, str(SCRIPT), "--require-qa-routes"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
    assert "SIGNUP_SURFACE_REACHABLE" in proc.stdout
    assert "QA_ROUTE_MARKERS_PRESENT" in proc.stdout
    assert '"ok": true' in proc.stdout
    report = json.loads(proc.stdout)
    # Correct-path markers must be asserted.
    for page in report["pages"]:
        assert "id=\"loginConsent\"" not in page.get("missing_markers", [])
        assert "id=\"loginGeoBtn\"" not in page.get("missing_markers", [])
        assert "Use my location" not in page.get("missing_markers", [])
        assert "Create wallet + QFOT" not in page.get("missing_markers", [])
        assert page.get("qa_routes_present") is True
    # Must not claim registration success.
    assert "account created" not in proc.stdout.lower()
    assert "registration success" not in proc.stdout.lower()


def test_signup_surface_markers_include_location_control():
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'id="loginGeoBtn"' in text
    assert "Use my location" in text
    assert 'id="loginConsent"' in text
    assert "Create wallet + QFOT" in text
    assert 'id="gamesBtn"' in text
    assert 'id="messageList"' in text
