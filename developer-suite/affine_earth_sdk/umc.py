"""Universal Manifold Controller — coding / cinema / aviation / gaming domains."""
from __future__ import annotations

from typing import Any, Optional

from .client import AffineClient

UMC_DOMAINS = ("cinema", "aviation", "gaming", "coding")


class UMCClient:
    def __init__(self, client: AffineClient) -> None:
        self.client = client

    def status(self) -> dict[str, Any]:
        r = self.client.get("/language-invariant/umc/status")
        r.raise_for_status()
        return r.json()

    def direct(
        self,
        domain: str = "coding",
        *,
        session_id: str = "dev-suite",
        node_id: str = "apex",
        title: str = "developer-suite",
        tau_height: int = 0,
        max_turns: int = 16,
        checkpoint: Optional[Any] = None,
    ) -> dict[str, Any]:
        domain = domain.lower().strip()
        if domain not in UMC_DOMAINS:
            domain = "coding"
        body: dict[str, Any] = {
            "domain": domain,
            "session_id": session_id,
            "node_id": node_id,
            "title": title,
            "tau_height": tau_height,
            "max_turns": max_turns,
        }
        if checkpoint is not None:
            body["checkpoint"] = checkpoint
        r = self.client.post(
            "/language-invariant/umc/direct",
            json=body,
            headers={"Content-Type": "application/json"},
        )
        r.raise_for_status()
        return r.json()

    def resume(
        self,
        domain: str,
        session_id: str,
        node_id: str = "apex",
        *,
        direct: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "domain": domain,
            "session_id": session_id,
            "node_id": node_id,
        }
        if direct is not None:
            body["direct"] = direct
        r = self.client.post(
            "/language-invariant/umc/resume",
            json=body,
            headers={"Content-Type": "application/json"},
        )
        r.raise_for_status()
        return r.json()
