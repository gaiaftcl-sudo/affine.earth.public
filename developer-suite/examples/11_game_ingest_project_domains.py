#!/usr/bin/env python3
"""All 12 LIVE games: teaching-shaped ingest → project → context."""
from _common import client, show
from affine_earth_sdk import LanguageGamesClient
from affine_earth_sdk.game_seeds import ALL_GAME_IDS, teaching_lesson, teaching_seed

with client() as c:
    lg = LanguageGamesClient(c)
    catalog = lg.games()
    show("catalog count", {"games": len(catalog.get("games", catalog))})
    failed: list[str] = []
    for gid in ALL_GAME_IDS:
        print(f"\n--- {gid} ---")
        print(f"LESSON: {teaching_lesson(gid)}")
        seed = teaching_seed(gid, session_suffix="ex11")
        try:
            ing = lg.game_ingest(gid, seed)
            proj = lg.game_project(gid, seed)
            ctx = lg.game_context(gid)
            show(
                f"{gid} ingest/project/context",
                {
                    "ingest_ok": bool(ing),
                    "project_ok": bool(proj),
                    "context_keys": list(ctx.keys())[:12] if isinstance(ctx, dict) else type(ctx).__name__,
                    "ingest": ing,
                    "project": proj,
                },
            )
        except Exception as exc:
            failed.append(gid)
            print(f"FAIL {gid}: {type(exc).__name__}: {exc}")
    if failed:
        raise SystemExit(f"INGEST_PROJECT_FAIL games={failed}")
    print("ALL_12_GAMES_INGEST_PROJECT_CONTEXT_PASS")
