#!/usr/bin/env python3
"""MCP tools/call execute_transition — geometry-only certified turn."""
from _common import client, show
from affine_earth_sdk import MCPClient

with client() as c:
    mcp = MCPClient(c)
    show("membrane_health", mcp.membrane_health())
    out = mcp.execute_transition(
        entity_id="devsuite-demo-entity",
        intent="OPEN_CURVE",
        s4=["1/1", "0/1", "0/1", "0/1"],
        c4=["1/1", "0/1", "0/1", "0/1"],
    )
    show("execute_transition", out)
