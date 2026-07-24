#!/usr/bin/env python3
"""Affine.Earth OS membrane via OpenAI-compatible /v1 wire (NOT api.openai.com).

Uses AFFINE_BASE_URL=https://affine.earth + AFFINE_API_KEY=uum8d-hle-verifier.
Model ids must come from live GET /v1/models only.
"""
from _common import client, show
from affine_earth_sdk import OpenAIV1Client

with client() as c:
    oa = OpenAIV1Client(c)
    models = oa.models()
    show("models", models)
    ids = {m.get("id") for m in (models.get("data") or []) if isinstance(m, dict)}
    model = "franklin-membrane" if "franklin-membrane" in ids else sorted(ids)[0]
    chat = oa.chat_completions(
        [{"role": "user", "content": "Say hello from Affine.Earth developer suite."}],
        model=model,
        max_tokens=128,
    )
    show("chat.completions", chat)
