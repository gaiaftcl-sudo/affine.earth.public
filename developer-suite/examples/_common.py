"""Shared helpers for examples/."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from affine_earth_sdk import AffineClient, AffineConfig  # noqa: E402


def client() -> AffineClient:
    return AffineClient(AffineConfig.from_env())


def show(label: str, obj) -> None:
    print(f"=== {label} ===")
    if isinstance(obj, (dict, list)):
        print(json.dumps(obj, indent=2, sort_keys=True)[:4000])
    else:
        print(str(obj)[:4000])
    print()
