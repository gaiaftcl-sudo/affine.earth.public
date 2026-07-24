#!/usr/bin/env python3
"""UMC coding domain + game ingest/project — LLVM narrative via live membrane.

Local LLVM compilation benchmarks stay in the parent package:
  python3 -m llm_llvm_bench.cli.main llvm --help
This example does NOT vendor a toolchain or OS binary.
"""
from pathlib import Path

from _common import ROOT, client, show
from affine_earth_sdk import LanguageGamesClient, UMCClient

snippet = (ROOT / "fixtures" / "coding" / "sample_snippet.c").read_text(encoding="utf-8")

with client() as c:
    umc = UMCClient(c)
    lg = LanguageGamesClient(c)
    show("umc status", umc.status())
    direct = umc.direct(
        "coding",
        session_id="devsuite-coding",
        title="llvm-narrative",
        max_turns=8,
    )
    show("umc.direct coding", direct)
    seed = {
        "node_id": "apex",
        "session_id": "devsuite-coding",
        "title": "sample_snippet.c",
        "tau_height": 0,
        "amplitudes": ["3/5", "4/5"],
        "statement": "Compile-check narrative for developer-suite fixture (text only).",
        "source_path": "fixtures/coding/sample_snippet.c",
        "source_chars": len(snippet),
    }
    show("coding ingest", lg.game_ingest("coding", seed))
    show("coding project", lg.game_project("coding", seed))
    print(
        "HINT: for local LLVM suite scores use sibling package:\n"
        "  cd .. && python3 -m llm_llvm_bench.cli.main llvm --help"
    )
