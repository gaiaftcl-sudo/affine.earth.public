#!/usr/bin/env python3
"""One-shot tour: health → MCP → OpenAI → game-turn → all 12 games → UMC → OpenUSD."""
from _common import client, show
from affine_earth_sdk import (
    LanguageGamesClient,
    MCPClient,
    OpenAIV1Client,
    OpenUSDClient,
    UMCClient,
)
from affine_earth_sdk.game_seeds import ALL_GAME_IDS, teaching_seed

with client() as c:
    steps = []
    try:
        hz = c.healthz()
        steps.append(("healthz", True, list(hz.keys())[:8]))
    except Exception as e:
        steps.append(("healthz", False, str(e)))

    mcp = MCPClient(c)
    try:
        tools = mcp.tools_list()
        names = [t.get("name") for t in ((tools.get("result") or {}).get("tools") or [])]
        steps.append(("mcp.tools", True, names))
    except Exception as e:
        steps.append(("mcp.tools", False, str(e)))

    oa = OpenAIV1Client(c)
    try:
        models = oa.models()
        ids = [m.get("id") for m in (models.get("data") or [])]
        steps.append(("openai.models", True, ids))
        resp = oa.responses("tour ping", store=False, max_output_tokens=64)
        steps.append(("openai.responses", True, resp.get("object")))
    except Exception as e:
        steps.append(("openai", False, str(e)))

    lg = LanguageGamesClient(c)
    try:
        turn = lg.game_turn(entity_id="tour")
        steps.append(("game-turn", True, (turn.get("game_ledger") or {}).get("status")))
    except Exception as e:
        steps.append(("game-turn", False, str(e)))

    # Teaching path: real ingest → project for every LIVE game
    game_fails: list[str] = []
    for gid in ALL_GAME_IDS:
        seed = teaching_seed(gid, session_suffix="tour")
        try:
            lg.game_ingest(gid, seed)
            lg.game_project(gid, seed)
        except Exception as e:
            game_fails.append(f"{gid}:{type(e).__name__}")
    steps.append(
        (
            "games.ingest_project_12",
            not game_fails,
            {"pass": len(ALL_GAME_IDS) - len(game_fails), "fail": game_fails},
        )
    )

    umc = UMCClient(c)
    try:
        d = umc.direct("coding", session_id="tour-affine-add", title="affine_add_app")
        steps.append(("umc.coding", True, d.get("status") or d.get("goal_satisfied")))
    except Exception as e:
        steps.append(("umc.coding", False, str(e)))

    usd = OpenUSDClient(c)
    try:
        s = usd.summary()
        steps.append(("openusd", True, {"bytes": s["bytes"], "defs": s["def_count"]}))
    except Exception as e:
        steps.append(("openusd", False, str(e)))

    show("domain tour", [{"step": a, "ok": b, "detail": c} for a, b, c in steps])
    fails = [a for a, b, _ in steps if not b]
    if fails:
        raise SystemExit(f"TOUR_FAIL {fails}")
    print("TOUR_PASS")
