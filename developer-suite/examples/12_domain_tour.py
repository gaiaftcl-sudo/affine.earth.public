#!/usr/bin/env python3
"""One-shot tour: health → MCP → OpenAI → game-turn → UMC coding → OpenUSD."""
from _common import client, show
from affine_earth_sdk import (
    LanguageGamesClient,
    MCPClient,
    OpenAIV1Client,
    OpenUSDClient,
    UMCClient,
)

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

    umc = UMCClient(c)
    try:
        d = umc.direct("coding", session_id="tour", title="tour")
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
