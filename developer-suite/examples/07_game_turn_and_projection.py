#!/usr/bin/env python3
"""Discrete game-turn (geometry only) — NATS language-game ledger."""
from _common import client, show
from affine_earth_sdk import LanguageGamesClient

with client() as c:
    lg = LanguageGamesClient(c)
    catalog = lg.games()
    show("games catalog (truncated)", {
        "count": len((catalog.get("games") or catalog.get("entries") or [])),
        "keys": list(catalog.keys())[:12],
    })
    turn = lg.game_turn(intent="OPEN_CURVE", entity_id="devsuite")
    show("game-turn", turn)
    gl = turn.get("game_ledger") or {}
    print("turn_subject:", gl.get("subject"))
    print("projection_subject:", gl.get("projection_subject"))
