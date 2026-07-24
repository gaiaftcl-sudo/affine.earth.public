"""Genesis-anchored seals — port of language-game/mcp-client.js."""
from __future__ import annotations

import hashlib

GENESIS_EPOCH = "2026-01-27T00:00:00Z"


def sha256_hex32(seed: str) -> str:
    dig = hashlib.sha256(seed.encode("utf-8")).digest()
    return dig.hex()[:32]


def genesis_anchored_signature(intent: str, scf_hex: str, user_hash: str) -> str:
    material = (
        f"{intent.upper()}|{scf_hex.lower()}|{user_hash.lower()}|{GENESIS_EPOCH}"
    )
    return sha256_hex32(material)


def game_turn_signature(intent: str, scf_hex: str, user_hash: str) -> str:
    """Discrete game-turn seal used by POST /language-invariant/game-turn."""
    material = f"{intent.upper()}|{scf_hex.lower()}|{user_hash.lower()}"
    return sha256_hex32(material)


def user_vqbit_hash(entity_id: str, scf_hex: str) -> str:
    return sha256_hex32(f"{entity_id.lower()}|{scf_hex.lower()}")


def mcp_scf_preview(
    entity_id: str,
    intent: str,
    s4: list[str] | None = None,
    c4: list[str] | None = None,
) -> str:
    """Client-side SCF preview (server may recompute; mismatch → re-sign)."""
    s4 = s4 or ["1/1", "0/1", "0/1", "0/1"]
    c4 = c4 or ["1/1", "0/1", "0/1", "0/1"]
    seed = (
        "mcp|v1|"
        + GENESIS_EPOCH
        + "|"
        + entity_id.lower()
        + "\0"
        + intent.upper()
        + "\0"
        + "".join(f"s4:{w}|" for w in s4)
        + "".join(f"c4:{w}|" for w in c4)
    )
    return sha256_hex32(seed)
