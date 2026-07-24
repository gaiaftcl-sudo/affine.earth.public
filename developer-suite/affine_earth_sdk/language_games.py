"""Language-game HTTP — inject, game-turn, catalog, ingest/project."""
from __future__ import annotations

import hashlib
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
    ) -> dict[str, Any]:
        scf = scf_hex or sha256_hex32(f"dev-suite|{entity_id}|{intent}")
        user = user_vqbit or user_vqbit_hash(entity_id, scf)
        # game-turn seal is intent|scf|user (no genesis epoch) — matches helper
        sig = game_turn_signature(intent, scf, user)
        # Some cells also accept vqbit_signature == sha256(intent|scf|user)[:32]
        # Prefer that exact form used by deploy-language-game-ui probe:
        sig = hashlib.sha256(
            f"{intent.upper()}|{scf.lower()}|{user.lower()}".encode()
        ).hexdigest()[:32]
        body = {
            "entity_id": entity_id,
            "scf_hex": scf.lower(),
            "intent": intent.upper(),
            "user_vqbit_hash": user.lower(),
            "vqbit_signature": sig,
            "bond_status": bond_status,
            "generative": 0,
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
