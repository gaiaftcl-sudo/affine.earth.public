# MCP (stateless HTTP)

Endpoint: `POST https://affine.earth/language-invariant/mcp`

JSON-RPC 2.0 methods used by this suite:

- `initialize`
- `tools/list`
- `tools/call` with `execute_transition`, `membrane_health`, `umc_direct`, …

`execute_transition` requires Rational `"num/den"` vectors and a genesis-anchored `client_signature`. The SDK re-signs when the membrane returns `BLOCKED_CLIENT_SIGNATURE_*` with `scf_hex`.

**Never** send raw chat text / images on the MCP turn wire (elephant → reject).

Python:

```python
from affine_earth_sdk import AffineClient, MCPClient
with AffineClient() as c:
    mcp = MCPClient(c)
    print(mcp.tools_list())
    print(mcp.execute_transition("my-entity", "OPEN_CURVE"))
```
