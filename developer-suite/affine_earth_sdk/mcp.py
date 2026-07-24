"""Stateless HTTP MCP client — POST /language-invariant/mcp."""
from __future__ import annotations

from typing import Any, Optional

from .client import AffineClient
from .seals import (
    genesis_anchored_signature,
    mcp_scf_preview,
    user_vqbit_hash,
)


class MCPClient:
    def __init__(self, client: AffineClient, path: str = "/language-invariant/mcp") -> None:
        self.client = client
        self.path = path
        self._rpc_id = 1

    def rpc(self, method: str, params: Any = None) -> dict[str, Any]:
        body: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": self._rpc_id,
            "method": method,
        }
        self._rpc_id += 1
        if params is not None:
            body["params"] = params
        r = self.client.post(self.path, json=body, headers={"Content-Type": "application/json"})
        r.raise_for_status()
        return r.json()

    def initialize(self) -> dict[str, Any]:
        return self.rpc(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "affine-earth-developer-suite", "version": "0.1.0"},
            },
        )

    def tools_list(self) -> dict[str, Any]:
        return self.rpc("tools/list")

    def tools_call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.rpc("tools/call", {"name": name, "arguments": arguments})

    def membrane_health(self) -> dict[str, Any]:
        return self.tools_call("membrane_health", {})

    def execute_transition(
        self,
        entity_id: str,
        intent: str = "OPEN_CURVE",
        *,
        s4: Optional[list[str]] = None,
        c4: Optional[list[str]] = None,
        bond_status: str = "UNKNOWN",
        user_vqbit: Optional[str] = None,
    ) -> dict[str, Any]:
        """Certified geometry turn with genesis re-sign on BLOCKED_CLIENT_SIGNATURE."""
        s4 = s4 or ["1/1", "0/1", "0/1", "0/1"]
        c4 = c4 or ["1/1", "0/1", "0/1", "0/1"]
        entity = entity_id.strip().lower()
        intent_u = intent.strip().upper()
        scf = mcp_scf_preview(entity, intent_u, s4, c4)
        user = user_vqbit or user_vqbit_hash(entity, scf)
        sig = genesis_anchored_signature(intent_u, scf, user)
        args = {
            "entity_id": entity,
            "user_vqbit_hash": user,
            "intent": intent_u,
            "s4_coordinates": s4,
            "c4_constraints": c4,
            "client_signature": sig,
            "bond_status": bond_status,
        }
        out = self.tools_call("execute_transition", args)
        structured = _structured(out)
        if (
            structured
            and str(structured.get("status") or "").startswith("BLOCKED_CLIENT_SIGNATURE")
            and structured.get("scf_hex")
        ):
            scf2 = str(structured["scf_hex"]).lower()
            user2 = user_vqbit or user_vqbit_hash(entity, scf2)
            args["user_vqbit_hash"] = user2
            args["client_signature"] = genesis_anchored_signature(intent_u, scf2, user2)
            out = self.tools_call("execute_transition", args)
        return out


def _structured(out: dict[str, Any]) -> Optional[dict[str, Any]]:
    result = out.get("result") if isinstance(out, dict) else None
    if not isinstance(result, dict):
        return None
    sc = result.get("structuredContent") or result.get("structured_content")
    return sc if isinstance(sc, dict) else None
