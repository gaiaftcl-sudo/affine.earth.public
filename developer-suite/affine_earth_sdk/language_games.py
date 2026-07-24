"""Language-game HTTP — inject, game-turn, catalog, ingest/project."""
from __future__ import annotations

from typing import Any, Optional

from .client import AffineClient
from .seals import game_turn_signature, sha256_hex32, user_vqbit_hash


class LanguageGamesClient:
    def __init__(self, client: AffineClient) -> None:
        self.client = client

    def games(self) -> dict[str, Any]:
        r = self.client.get("/language-invariant/games")
        r.raise_for_status()
        return r.json()

    def inject(
        self,
        a: str,
        b: str,
        *,
        scf_hex: Optional[str] = None,
        **extra: Any,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"a": a, "b": b}
        if scf_hex:
            body["scf_hex"] = scf_hex
        body.update(extra)
        r = self.client.post(
            "/language-invariant/inject",
            json=body,
            headers={"Content-Type": "application/json"},
        )
        r.raise_for_status()
        return r.json()

    def game_turn(
        self,
        *,
        scf_hex: Optional[str] = None,
        intent: str = "OPEN_CURVE",
        entity_id: str = "anon",
        bond_status: str = "UNKNOWN",
        user_vqbit: Optional[str] = None,
        generative: int = 0,
    ) -> dict[str, Any]:
        # entity_id is local seed only — apex REJECTED_ELEPHANT forbids it on wire.
        scf = scf_hex or sha256_hex32(f"dev-suite|{entity_id}|{intent}")
        user = user_vqbit or user_vqbit_hash(entity_id, scf)
        sig = game_turn_signature(intent, scf, user)
        body = {
            "scf_hex": scf.lower(),
            "intent": intent.upper(),
            "user_vqbit_hash": user.lower(),
            "vqbit_signature": sig,
            "bond_status": bond_status,
            "generative": int(generative),
        }
        r = self.client.post(
            "/language-invariant/game-turn",
            json=body,
            headers={"Content-Type": "application/json"},
        )
        r.raise_for_status()
        return r.json()

    def game_context(self, game_id: str) -> dict[str, Any]:
        r = self.client.get(f"/language-invariant/game/{game_id}/context")
        r.raise_for_status()
        return r.json()

    def game_ingest(self, game_id: str, body: dict[str, Any]) -> dict[str, Any]:
        r = self.client.post(
            f"/language-invariant/game/{game_id}/ingest",
            json=body,
            headers={"Content-Type": "application/json"},
        )
        r.raise_for_status()
        return r.json()

    def game_project(self, game_id: str, body: dict[str, Any]) -> dict[str, Any]:
        r = self.client.post(
            f"/language-invariant/game/{game_id}/project",
            json=body,
            headers={"Content-Type": "application/json"},
        )
        r.raise_for_status()
        return r.json()
