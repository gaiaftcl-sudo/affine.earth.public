#!/usr/bin/env python3
"""UMC coding + AffineAddApp teaching application via live ingest/project.

Local LLVM compilation benchmarks stay in the parent package:
  python3 -m llm_llvm_bench.cli.main llvm --help
This example does NOT vendor a toolchain or OS binary.
"""
import subprocess
import sys
from pathlib import Path

from _common import ROOT, client, show
from affine_earth_sdk import LanguageGamesClient, UMCClient
from affine_earth_sdk.game_seeds import teaching_seed

APP = ROOT / "fixtures" / "coding" / "affine_add_app"
main_py = APP / "main.py"
addlib = APP / "addlib.c"

# Prove the teaching app runs locally (binary-free Python)
local = subprocess.run([sys.executable, str(main_py)], capture_output=True, text=True, check=False)
show(
    "AffineAddApp local run",
    {
        "exit_code": local.returncode,
        "stdout": (local.stdout or "").strip(),
        "c_twin_chars": len(addlib.read_text(encoding="utf-8")),
    },
)
if local.returncode != 0:
    raise SystemExit("AffineAddApp local run failed")

with client() as c:
    umc = UMCClient(c)
    lg = LanguageGamesClient(c)
    show("umc status", umc.status())
    direct = umc.direct(
        "coding",
        session_id="devsuite-affine-add-app",
        title="affine_add_app",
        max_turns=8,
    )
    show("umc.direct coding", direct)
    seed = teaching_seed("coding", session_suffix="ex08-app")
    seed["statement"] = "AffineAddApp: 2+2→4 teaching compile narrative"
    seed["source_path"] = "fixtures/coding/affine_add_app/main.py"
    seed["source_chars"] = len(main_py.read_text(encoding="utf-8"))
    show("coding ingest (AffineAddApp)", lg.game_ingest("coding", seed))
    show("coding project (AffineAddApp)", lg.game_project("coding", seed))
    show("coding context", lg.game_context("coding"))
    print("CODING_APP_MEMBRANE_PASS")
    print(
        "HINT: for local LLVM suite scores use sibling package:\n"
        "  cd .. && python3 -m llm_llvm_bench.cli.main llvm --help"
    )
