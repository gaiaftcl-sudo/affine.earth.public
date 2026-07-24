#!/usr/bin/env python3
"""Run all 12 language games with real ingest + project; write teaching receipt.

Receipt: docs/receipts/LANGUAGE_GAMES_TEACHING_RUN.json
Markdown companion regenerated: docs/LANGUAGE_GAMES_TEACHING.md (body section)
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from _common import ROOT, client
from affine_earth_sdk import LanguageGamesClient
from affine_earth_sdk.game_seeds import ALL_GAME_IDS, teaching_lesson, teaching_seed

RECEIPT_PATH = ROOT / "docs" / "receipts" / "LANGUAGE_GAMES_TEACHING_RUN.json"
MD_PATH = ROOT / "docs" / "LANGUAGE_GAMES_TEACHING.md"
APP_DIR = ROOT / "fixtures" / "coding" / "affine_add_app"


def _run_coding_app() -> dict:
    main_py = APP_DIR / "main.py"
    proc = subprocess.run(
        [sys.executable, str(main_py)],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "exit_code": proc.returncode,
        "stdout": (proc.stdout or "").strip(),
        "stderr": (proc.stderr or "").strip(),
        "app_path": str(APP_DIR.relative_to(ROOT)),
    }


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    app_run = _run_coding_app()
    rows: list[dict] = []
    failed: list[str] = []

    with client() as c:
        lg = LanguageGamesClient(c)
        apex = c.config.base_url.rstrip("/")
        _ = lg.games()
        for gid in ALL_GAME_IDS:
            seed = teaching_seed(gid, session_suffix="teach-run")
            row: dict = {
                "game_id": gid,
                "lesson": teaching_lesson(gid),
                "seed_keys": sorted(seed.keys()),
            }
            try:
                ing = lg.game_ingest(gid, seed)
                proj = lg.game_project(gid, seed)
                ctx = lg.game_context(gid)
                row.update(
                    {
                        "status": "PASS",
                        "ingest_http": 200,
                        "project_http": 200,
                        "context_http": 200,
                        "ingest": ing,
                        "project": proj,
                        "context_summary": {
                            "keys": list(ctx.keys())[:16] if isinstance(ctx, dict) else [],
                        },
                    }
                )
                print(f"PASS {gid}")
            except Exception as exc:
                failed.append(gid)
                row.update({"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"})
                print(f"FAIL {gid}: {exc}")
            rows.append(row)

    receipt = {
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "apex": apex,
        "coding_app_local": app_run,
        "games_total": len(ALL_GAME_IDS),
        "games_pass": len(ALL_GAME_IDS) - len(failed),
        "games_fail": failed,
        "overall": "PASS" if not failed and app_run["exit_code"] == 0 else "FAIL",
        "rows": rows,
    }
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(receipt)
    print(f"\nreceipt={RECEIPT_PATH}")
    print(f"markdown={MD_PATH}")
    print(f"overall={receipt['overall']}")
    return 0 if receipt["overall"] == "PASS" else 1


def _write_markdown(receipt: dict) -> None:
    lines = [
        "# Language games — teaching suite (measured)",
        "",
        "Real membrane path: **ingest → project → context** for all 12 LIVE games,",
        "plus the local **AffineAddApp** coding application (binary-free).",
        "",
        f"- Apex: `{receipt['apex']}`",
        f"- Started: `{receipt['started_at']}`",
        f"- Finished: `{receipt['finished_at']}`",
        f"- Overall: **{receipt['overall']}** "
        f"({receipt['games_pass']}/{receipt['games_total']} games; "
        f"coding app exit={receipt['coding_app_local']['exit_code']})",
        f"- Machine receipt: [`receipts/LANGUAGE_GAMES_TEACHING_RUN.json`]"
        f"(receipts/LANGUAGE_GAMES_TEACHING_RUN.json)",
        "",
        "## Coding application (local)",
        "",
        "Path: `fixtures/coding/affine_add_app/`",
        "",
        "```text",
        receipt["coding_app_local"].get("stdout", ""),
        "```",
        "",
        "Wire into coding game via `workspace_hint=fixtures/coding/affine_add_app`",
        "(see `examples/08_umc_coding_llvm_narrative.py` and `examples/games/coding.py`).",
        "",
        "## How to re-run",
        "",
        "```bash",
        "cd developer-suite",
        "python3 examples/13_all_language_games_teaching.py",
        "python3 examples/11_game_ingest_project_domains.py",
        "python3 examples/games/run_all.py",
        "```",
        "",
        "## Per-game teaching results",
        "",
    ]
    for row in receipt["rows"]:
        gid = row["game_id"]
        lines.append(f"### `{gid}` — {row['status']}")
        lines.append("")
        lines.append(row.get("lesson") or "")
        lines.append("")
        lines.append(f"- Seed keys: `{', '.join(row.get('seed_keys', []))}`")
        if row["status"] == "PASS":
            lines.append("- HTTP: ingest 200 · project 200 · context 200")
            ing = row.get("ingest") or {}
            proj = row.get("project") or {}
            # keep doc short — show terminals / status fields if present
            for label, blob in (("ingest", ing), ("project", proj)):
                if isinstance(blob, dict):
                    snippet = {
                        k: blob[k]
                        for k in ("status", "terminal", "game_id", "ok", "calorie", "cure")
                        if k in blob
                    }
                    if snippet:
                        lines.append(f"- {label} fields: `{json.dumps(snippet)}`")
        else:
            lines.append(f"- Error: `{row.get('error')}`")
        lines.append("")
        lines.append(f"Teaching script: `examples/games/{gid}.py`")
        lines.append("")
    lines.extend(
        [
            "## Architecture (developer view)",
            "",
            "```text",
            "teaching seed (game_seeds.py)",
            "        │",
            "        ▼",
            "POST /language-invariant/game/{id}/ingest   ← real ingestion",
            "        │",
            "        ▼",
            "POST /language-invariant/game/{id}/project  ← real projection",
            "        │",
            "        ▼",
            "GET  /language-invariant/game/{id}/context  ← observer context",
            "```",
            "",
            "No OS binaries. No mocks. Apex Affine.Earth OS membrane only.",
            "",
        ]
    )
    MD_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
