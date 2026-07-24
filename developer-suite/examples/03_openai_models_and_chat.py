#!/usr/bin/env python3
"""OpenAI GET /v1/models + POST /v1/chat/completions (Bearer required)."""
from _common import client, show
from affine_earth_sdk import OpenAIV1Client

with client() as c:
    oa = OpenAIV1Client(c)
    show("models", oa.models())
    chat = oa.chat_completions(
        [{"role": "user", "content": "Say hello from Affine.Earth developer suite."}],
        model="franklin-membrane",
        max_tokens=128,
    )
    show("chat.completions", chat)
