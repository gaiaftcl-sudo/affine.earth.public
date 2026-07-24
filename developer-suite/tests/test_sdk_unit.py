"""Offline unit tests — no network."""
from __future__ import annotations

from affine_earth_sdk.seals import (
    GENESIS_EPOCH,
    genesis_anchored_signature,
    mcp_scf_preview,
    sha256_hex32,
    user_vqbit_hash,
)


def test_sha256_hex32_len():
    assert len(sha256_hex32("x")) == 32


def test_genesis_epoch_constant():
    assert GENESIS_EPOCH == "2026-01-27T00:00:00Z"


def test_genesis_signature_stable():
    a = genesis_anchored_signature("OPEN_CURVE", "abc", "def")
    b = genesis_anchored_signature("open_curve", "ABC", "DEF")
    assert a == b
    assert len(a) == 32


def test_user_and_preview():
    scf = mcp_scf_preview("entity", "OPEN_CURVE")
    assert len(scf) == 32
    u = user_vqbit_hash("entity", scf)
    assert len(u) == 32
