"""Opt-in live smoke against AFFINE_BASE_URL (default https://affine.earth)."""
from __future__ import annotations

import os

import pytest

from affine_earth_sdk import (
    AffineClient,
    AffineConfig,
    LanguageGamesClient,
    MCPClient,
    OpenAIV1Client,
    OpenUSDClient,
    UMCClient,
)

pytestmark = pytest.mark.live


def _live_enabled() -> bool:
    return (os.environ.get("AFFINE_LIVE") or "").strip() in ("1", "true", "yes")


@pytest.fixture(scope="module")
def client():
    if not _live_enabled():
        pytest.skip("set AFFINE_LIVE=1 to hit live apex")
    with AffineClient(AffineConfig.from_env()) as c:
        yield c


def test_healthz(client):
    hz = client.healthz()
    assert isinstance(hz, dict)


def test_mcp_tools(client):
    mcp = MCPClient(client)
    out = mcp.tools_list()
    tools = (out.get("result") or {}).get("tools") or []
    names = {t.get("name") for t in tools if isinstance(t, dict)}
    assert "execute_transition" in names


def test_openai_models_chat_responses(client):
    oa = OpenAIV1Client(client)
    models = oa.models()
    ids = {m.get("id") for m in (models.get("data") or [])}
    assert "franklin-membrane" in ids or "gaiaftcl-os" in ids
    chat = oa.chat_completions(
        [{"role": "user", "content": "ping"}],
        max_tokens=64,
    )
    assert chat.get("object") == "chat.completion"
    resp = oa.responses("ping", store=False, max_output_tokens=64)
    assert resp.get("object") == "response"


def test_game_turn(client):
    lg = LanguageGamesClient(client)
    turn = lg.game_turn(entity_id="pytest-live")
    assert "game_ledger" in turn or turn.get("status")


def test_umc_coding(client):
    umc = UMCClient(client)
    out = umc.direct("coding", session_id="pytest-live", title="pytest")
    assert isinstance(out, dict)


def test_openusd(client):
    usd = OpenUSDClient(client)
    s = usd.summary()
    assert s["bytes"] > 100
    assert usd.airspace_html_ok()
