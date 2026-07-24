#!/usr/bin/env python3
"""MCP initialize + tools/list on POST /language-invariant/mcp."""
from _common import client, show
from affine_earth_sdk import MCPClient

with client() as c:
    mcp = MCPClient(c)
    show("initialize", mcp.initialize())
    tools = mcp.tools_list()
    show("tools/list", tools)
    names = [
        t.get("name")
        for t in ((tools.get("result") or {}).get("tools") or [])
        if isinstance(t, dict)
    ]
    print("tool_names:", names)
