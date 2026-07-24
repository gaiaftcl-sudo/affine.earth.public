#!/usr/bin/env python3
"""OpenAI Responses API — POST /v1/responses (store:false)."""
from _common import client, show
from affine_earth_sdk import OpenAIV1Client

with client() as c:
    oa = OpenAIV1Client(c)
    resp = oa.responses(
        "Ping Affine.Earth Responses API from the developer suite.",
        model="franklin-membrane",
        store=False,
        max_output_tokens=128,
    )
    show("responses", resp)
    print("output_text:", (resp.get("output_text") or "")[:500])
