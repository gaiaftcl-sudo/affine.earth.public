# Domains

Affine.Earth language games expose multiple domains through one HTTPS membrane.

| Domain | Primary surfaces |
|--------|------------------|
| **MCP** | `POST /language-invariant/mcp` — `execute_transition`, `membrane_health`, `umc_*` |
| **OpenAI /v1** | models, chat completions, responses, api-keys |
| **Coding / LLVM narrative** | UMC `domain=coding` + game ingest/project; local LLVM via `llm_llvm_bench` |
| **Cinema** | UMC + `game/cinema/ingest\|project` |
| **Aviation / ATC** | UMC + `game/aviation*` ingest/project + airspace USDA |
| **Gaming** | UMC + `game/gaming` |
| **OpenUSD / Reality** | `/language-game/*.usda`, RealityPro player, observer-demo |
| **Core turns** | inject, game-turn (geometry only — no chat elephant) |

All **12 LIVE** games (cinema, aviation, aviation_atc, gaming, coding, reality,
topological_sandbox, formal_manifold, wallet_qfot, linguistic_membrane, umc_gav,
torsion_dialogue) have teaching seeds in `affine_earth_sdk/game_seeds.py` and
per-game scripts under `examples/games/`.

Measured ingest → project → context run: [LANGUAGE_GAMES_TEACHING.md](LANGUAGE_GAMES_TEACHING.md).

Coding teaching app: `fixtures/coding/affine_add_app/` (wired by examples `08` + `games/coding.py`).

See examples `08`–`13`, `examples/games/run_all.py`, and the RealityPro player.
