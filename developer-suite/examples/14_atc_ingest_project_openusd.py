#!/usr/bin/env python3
"""ATC solution recipe — health → aviation_atc ingest/project/context → OpenUSD airspace.

Measured against live Affine.Earth OS membrane (not cloud OpenAI/Anthropic).
See docs/ATC_INGEST_PROJECT.md.
"""
from __future__ import annotations

from _common import client, show
from affine_earth_sdk import LanguageGamesClient, OpenUSDClient
from affine_earth_sdk.game_seeds import teaching_lesson, teaching_seed

RICHER_CLEARANCE = {
    "sector_id": "ZNY-42",
    "callsign": "UAL772",
    "clearance_kind": "VECTOR",
    "altitude_ft": 24000,
    "route": "EWR..BOS",
    "node_id": "apex",
    "session_id": "ex14-atc-rich",
    "tau_height": 0,
    "amplitudes": ["3/5", "4/5"],
    "title": "ATC richer VECTOR clearance UAL772",
    "locale": "en",
    "statement": "Vector UAL772 heading 070 maintain FL240 sector ZNY-42",
}


def main() -> int:
    print(teaching_lesson("aviation_atc"))
    with client() as c:
        hz = c.healthz()
        show("healthz", {"ok": hz.get("ok"), "cloud_openai": hz.get("cloud_openai"), "mcp": hz.get("mcp")})
        if not hz.get("ok"):
            raise SystemExit("HEALTHZ_FAIL")

        lg = LanguageGamesClient(c)
        catalog = lg.games()
        games = catalog.get("games") or []
        atc = next((g for g in games if g.get("game_id") == "aviation_atc"), None)
        show(
            "aviation_atc catalog entry",
            {
                "game_count": catalog.get("game_count"),
                "status": (atc or {}).get("status"),
                "nats_subject_prefix": (atc or {}).get("nats_subject_prefix"),
                "concept_kinds": (atc or {}).get("concept_kinds"),
                "http": (atc or {}).get("http"),
            },
        )
        if not atc or atc.get("status") != "LIVE":
            raise SystemExit("AVIATION_ATC_NOT_LIVE")

        teach = teaching_seed("aviation_atc", session_suffix="ex14")
        show("teaching seed", teach)
        ing = lg.game_ingest("aviation_atc", teach)
        show(
            "ingest teaching",
            {
                "status": ing.get("status"),
                "calorie": ing.get("calorie"),
                "concept_ids": ing.get("concept_ids"),
                "nats_subject": (ing.get("manifold_seed") or {}).get("nats_subject"),
                "sector_session": (ing.get("manifold_seed") or {}).get("session_id"),
            },
        )
        proj = lg.game_project("aviation_atc", teach)
        show(
            "project teaching",
            {
                "game_id": proj.get("game_id"),
                "primitive": proj.get("primitive"),
                "projected_kinds": proj.get("projected_kinds"),
                "concept_ids": proj.get("concept_ids"),
                "zero_shear": proj.get("zero_shear"),
            },
        )

        show("richer clearance seed", RICHER_CLEARANCE)
        ing_r = lg.game_ingest("aviation_atc", RICHER_CLEARANCE)
        show(
            "ingest richer",
            {
                "status": ing_r.get("status"),
                "calorie": ing_r.get("calorie"),
                "concept_ids": ing_r.get("concept_ids"),
                "title": (ing_r.get("manifold_seed") or {}).get("title"),
            },
        )
        proj_r = lg.game_project("aviation_atc", RICHER_CLEARANCE)
        show(
            "project richer",
            {
                "projected_kinds": proj_r.get("projected_kinds"),
                "primitive": proj_r.get("primitive"),
                "concept_ids": proj_r.get("concept_ids"),
            },
        )

        ctx = lg.game_context("aviation_atc")
        show(
            "context",
            {
                "context_agent": ctx.get("context_agent"),
                "game_id": ctx.get("game_id"),
                "display_kind": (ctx.get("entry") or {}).get("display_kind"),
                "payload_shape": (ctx.get("entry") or {}).get("payload_shape"),
                "prior_turn_count": (ctx.get("next_move") or {}).get("prior_turn_count"),
            },
        )

        usd = OpenUSDClient(c)
        summary = usd.summary()
        show("OpenUSD airspace-lattice.usda", summary)
        print("airspace.html OK:", usd.airspace_html_ok())
        print()
        print("Open RealityPro ATC scene:")
        print("  https://affine.earth/language-game/realitypro/")
        print("  1) USDA path = /language-game/airspace-lattice.usda → Load USDA → Preview")
        print("  2) Game select = aviation_atc → Ingest → Project (membrane ticks pulse lattice)")
        print("  3) NATS-shaped subjects: gaiaftcl.aviation.flow.* + gaiaftcl.reality.manifold.realitypro.apex")

        if ing.get("status") != "CALORIE_GAME_INGEST" or ing.get("calorie") != "CALORIE_ATC_SECTOR_FLOW":
            raise SystemExit("ATC_INGEST_CALORIE_FAIL")
        if "ATC_SECTOR" not in (proj.get("projected_kinds") or {}):
            raise SystemExit("ATC_PROJECT_KINDS_FAIL")
        if summary.get("def_count", 0) < 1:
            raise SystemExit("USDA_EMPTY")

    print("ATC_INGEST_PROJECT_OPENUSD_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
