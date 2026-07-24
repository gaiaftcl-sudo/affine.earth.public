#!/usr/bin/env python3
"""Run every per-game teaching example sequentially."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from affine_earth_sdk.game_seeds import ALL_GAME_IDS  # noqa: E402

HERE = Path(__file__).resolve().parent


def main() -> int:
    failed = []
    for gid in ALL_GAME_IDS:
        script = HERE / f"{gid}.py"
        print(f"\n######## {gid} ########")
        r = subprocess.run([sys.executable, str(script)], check=False)
        if r.returncode != 0:
            failed.append(gid)
    if failed:
        print(f"GAMES_FAIL {failed}")
        return 1
    print("ALL_GAME_TEACHING_EXAMPLES_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
