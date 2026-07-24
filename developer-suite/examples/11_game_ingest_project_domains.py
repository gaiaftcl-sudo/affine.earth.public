#!/usr/bin/env python3
"""Game ingest + project across aviation / cinema / gaming / coding."""
from _common import client, show
from affine_earth_sdk import LanguageGamesClient

DOMAINS = ("aviation", "aviation_atc", "cinema", "gaming", "coding", "reality")

with client() as c:
    lg = LanguageGamesClient(c)
    catalog = lg.games()
    show("catalog keys", list(catalog.keys())[:20])
    for gid in DOMAINS:
        seed = {
            "node_id": "apex",
            "session_id": f"devsuite-{gid}",
            "title": f"developer-suite-{gid}",
            "tau_height": 0,
            "amplitudes": ["3/5", "4/5"],
        }
        try:
            ing = lg.game_ingest(gid, seed)
            proj = lg.game_project(gid, seed)
            show(f"{gid} ingest/project", {"ingest": ing, "project": proj})
        except Exception as exc:
            print(f"FAIL {gid}: {type(exc).__name__}: {exc}")
