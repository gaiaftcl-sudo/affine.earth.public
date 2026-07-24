#!/usr/bin/env python3
"""HLE exam profile smoke — franklin-membrane-exam + X-Affine-Exam: hle.

Full HLE/ARC harnesses live in the parent public suite (scripts/*openai*exam*.py).
This example only proves the OpenAI exam membrane returns Answer:/Confidence:.
"""
from _common import client, show
from affine_earth_sdk import OpenAIV1Client

with client() as c:
    oa = OpenAIV1Client(c)
    chat = oa.chat_completions(
        [
            {
                "role": "system",
                "content": (
                    "End with EXACTLY:\n"
                    "Explanation: <one short sentence>\n"
                    "Answer: <final value only>\n"
                    "Confidence: <NN>%"
                ),
            },
            {"role": "user", "content": "What is 2+2?"},
        ],
        model="franklin-membrane-exam",
        exam=True,
        max_tokens=128,
        temperature=0,
    )
    show("exam chat", chat)
    text = ((chat.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    print("assistant:\n", text)
    resp = oa.responses(
        "What is 2+2?",
        model="franklin-membrane-exam",
        instructions="End with Explanation/Answer/Confidence. Answer value only.",
        exam=True,
        store=False,
        max_output_tokens=128,
    )
    show("exam responses", {"output_text": resp.get("output_text"), "object": resp.get("object")})
