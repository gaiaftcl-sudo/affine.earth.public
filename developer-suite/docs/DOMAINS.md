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

See examples `08`–`12` and the RealityPro player for end-to-end walks.
