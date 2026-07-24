"""Teaching seeds for all 12 LIVE language games — real ingest/project payloads."""
from __future__ import annotations

from typing import Any, Callable

SeedFn = Callable[[str], dict[str, Any]]

# Catalog order matches GET /language-invariant/games
ALL_GAME_IDS = (
    "cinema",
    "aviation",
    "aviation_atc",
    "gaming",
    "coding",
    "reality",
    "topological_sandbox",
    "formal_manifold",
    "wallet_qfot",
    "linguistic_membrane",
    "umc_gav",
    "torsion_dialogue",
)


def _amps() -> list[str]:
    # Pythagorean unit pair → torsion 0/1 (CALORIE path)
    return ["3/5", "4/5"]


def teaching_seed(game_id: str, session_suffix: str = "teach") -> dict[str, Any]:
    """Domain-shaped seed for POST .../game/{id}/ingest and .../project."""
    gid = game_id.lower().strip()
    sess = f"{session_suffix}-{gid}"
    builders: dict[str, SeedFn] = {
        "cinema": lambda s: {
            "film_id": "affine-horizon",
            "title": "Affine Horizon — teaching reel",
            "characters": ["Franklin", "Steward", "Observer"],
            "structural_bound": "FEATURE_LENGTH",
            "H_start": "0/1",
            "H_end": "1/1",
            "node_id": "apex",
            "session_id": s,
            "tau_height": 0,
            "amplitudes": _amps(),
            "locale": "en",
            "statement": "Narrative manifold seed for cinema teaching example",
        },
        "aviation": lambda s: {
            "role": "AVIATION_PILOT",
            "flight_id": "GAIA001",
            "node_id": "apex",
            "session_id": s,
            "tau_height": 0,
            "amplitudes": _amps(),
            "title": "Pilot role matrix teaching flight",
            "locale": "en",
        },
        "aviation_atc": lambda s: {
            "sector_id": "ZNY-42",
            "callsign": "GAIA001",
            "clearance_kind": "CLIMB",
            "node_id": "apex",
            "session_id": s,
            "tau_height": 0,
            "amplitudes": _amps(),
            "title": "ATC sector flow teaching clearance",
            "locale": "en",
        },
        "gaming": lambda s: {
            "session_id": s,
            "node_id": "apex",
            "title": "rule-desync teaching match",
            "layer_labels": ["RULE_VIOLATION", "DESYNC"],
            "amplitudes": _amps(),
            "tau_height": 0,
            "locale": "en",
        },
        "coding": lambda s: {
            "session_id": s,
            "node_id": "apex",
            "title": "affine_add_app — teaching coding application",
            "workspace_hint": "fixtures/coding/affine_add_app",
            "amplitudes": _amps(),
            "tau_height": 0,
            "statement": "Long-play coding: ingest affine_add_app then project compile narrative",
            "locale": "en",
        },
        "reality": lambda s: {
            "room_id": "room-teach",
            "presence_id": "presence-teach-1",
            "node_id": "apex",
            "torsion_num": 0,
            "torsion_den": 1,
            "session_id": s,
            "amplitudes": _amps(),
            "title": "Reality immersion teaching room",
            "locale": "en",
        },
        "topological_sandbox": lambda s: {
            "action": "heal",
            "torsion_num": 0,
            "torsion_den": 1,
            "node_id": "apex",
            "session_id": s,
            "amplitudes": _amps(),
            "title": "Sandbox heal teaching stroke",
            "locale": "en",
        },
        "formal_manifold": lambda s: {
            "domain": "coding",
            "amplitudes": _amps(),
            "statement": "2+2 collapses to 4 on the formal manifold",
            "node_id": "apex",
            "tau_height": 0,
            "session_id": s,
            "title": "Formal observer teaching collapse",
            "locale": "en",
        },
        "wallet_qfot": lambda s: {
            # Teaching-only placeholder address (not a live spend key)
            "address": "bc1qaffineearthteach0000000000000000000",
            "lat_micro": 40712800,
            "lon_micro": -74006000,
            "amount_num": 0,
            "amount_den": 1,
            "domain": "coding",
            "node_id": "apex",
            "session_id": s,
            "amplitudes": ["1/1", "0/1"],
            "title": "Wallet/QFOT teaching bind (zero transfer)",
            "locale": "en",
        },
        "linguistic_membrane": lambda s: {
            "intent": "OPEN_CURVE",
            "scf_hash": "a" * 32,
            "user_vqbit_hash": "b" * 32,
            "vqbit_signature": "c" * 32,
            "locale": "en",
            "node_id": "apex",
            "session_id": s,
            "amplitudes": _amps(),
            "title": "Linguistic membrane teaching turn envelope",
        },
        "umc_gav": lambda s: {
            "domain": "coding",
            "session_id": s,
            "node_id": "apex",
            "title": "UMC GAV teaching long play",
            "max_turns": 8,
            "tau_height": 0,
            "amplitudes": _amps(),
            "locale": "en",
        },
        "torsion_dialogue": lambda s: {
            "room_id": "room-teach",
            "agreement": 1,
            "operator_tensor": "AGREE",
            "node_id": "apex",
            "session_id": s,
            "amplitudes": _amps(),
            "title": "Torsion dialogue agreement fuse",
            "locale": "en",
        },
    }
    if gid not in builders:
        raise KeyError(f"unknown game_id {gid}; known={ALL_GAME_IDS}")
    return builders[gid](sess)


def teaching_lesson(game_id: str) -> str:
    """One-paragraph teaching note per game."""
    lessons = {
        "cinema": "Ingest a NarrativeManifoldSeed (film + characters); project locale Concept_IDs onto the cinema Gyroid.",
        "aviation": "Ingest an AviationRole + flight_id; project role/telemetry Concept_IDs for the aviation manifold.",
        "aviation_atc": "Ingest ATC sector/callsign/clearance (not chat); project sector-flow Concept_IDs.",
        "gaming": "Ingest rule/desync labels for a session; project Gyroid/Shatter for gaming UMC state.",
        "coding": "Ingest a coding workspace (affine_add_app); project MCP/compile narrative via CodingContextAgent.",
        "reality": "Ingest RealityRoom presence OperatorTensor; project room.manifold Gyroid fuse.",
        "topological_sandbox": "Ingest heal|shatter OperatorTensor; project Mirror Manifold WebGL primitives.",
        "formal_manifold": "Ingest LogicalAmplitudeTensor (statement + amplitudes); project COLLAPSE/DIVERGENCE.",
        "wallet_qfot": "Ingest wallet bind / zero QFOT transfer (Rational); project profile + economics subjects.",
        "linguistic_membrane": "Ingest intent+SCF+signature envelope; project sovereign linguistic kinds (no elephant text).",
        "umc_gav": "Ingest UMC Director ManifoldSeed; project Long Play viewport subjects.",
        "torsion_dialogue": "Ingest collaborative agreement OperatorTensor; project τ→0 fuse / local Shatter.",
    }
    return lessons.get(game_id, "")
