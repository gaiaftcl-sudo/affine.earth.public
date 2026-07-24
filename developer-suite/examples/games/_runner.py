"""Shared runner for per-game teaching examples."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EX = Path(__file__).resolve().parents[1]
if str(EX) not in sys.path:
    sys.path.insert(0, str(EX))

from _common import client, show  # noqa: E402
from affine_earth_sdk import LanguageGamesClient  # noqa: E402
from affine_earth_sdk.game_seeds import teaching_lesson, teaching_seed  # noqa: E402


def run_game(game_id: str) -> int:
    print(f"GAME={game_id}")
    print(f"LESSON={teaching_lesson(game_id)}")
    seed = teaching_seed(game_id, session_suffix=f"ex-{game_id}")
    show("teaching seed", seed)
    with client() as c:
        lg = LanguageGamesClient(c)
        ing = lg.game_ingest(game_id, seed)
        proj = lg.game_project(game_id, seed)
        ctx = lg.game_context(game_id)
        show("ingest (real)", ing)
        show("project (real)", proj)
        show("context (real)", ctx if not isinstance(ctx, dict) else {k: ctx[k] for k in list(ctx)[:20]})
    print(f"TEACHING_PASS game={game_id}")
    return 0
