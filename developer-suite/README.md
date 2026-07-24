# Affine.Earth Developer Example Suite

Binary-free Python SDK + examples + RealityPro web player for the live Affine.Earth OS membrane.

**Repo:** [gaiaftcl-sudo/affine.earth.public](https://github.com/gaiaftcl-sudo/affine.earth.public) → `developer-suite/`  
**Does not ship** GaiaFTCLCLI, GGUF, `.app`, or any OS binary. See [docs/NO_BINARIES.md](docs/NO_BINARIES.md).

## Install

```bash
git clone https://github.com/gaiaftcl-sudo/affine.earth.public.git
cd affine.earth.public/developer-suite
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # edit AFFINE_API_KEY if needed
```

Default apex: `https://affine.earth`  
Bootstrap Bearer (exam / chat): `uum8d-hle-verifier` (mint more via `POST /v1/api-keys`).

## Quick prove

```bash
python3 scripts/check_no_binaries.py
pytest tests/test_sdk_unit.py -v
AFFINE_LIVE=1 pytest tests/test_live_smoke.py -v -m live
python3 examples/12_domain_tour.py
```

## Examples

| Script | Surface |
|--------|---------|
| `00_healthz.py` | `GET /language-invariant/healthz` |
| `01_mcp_tools_list.py` | MCP `initialize` + `tools/list` |
| `02_mcp_execute_transition.py` | MCP `execute_transition` |
| `03_openai_models_and_chat.py` | `/v1/models` + chat completions |
| `04_openai_responses.py` | `/v1/responses` (`store:false`) |
| `05_exam_hle_smoke.py` | Exam profile + `X-Affine-Exam: hle` |
| `06_inject_and_scf.py` | Language inject |
| `07_game_turn_and_projection.py` | Discrete game-turn |
| `08_umc_coding_llvm_narrative.py` | UMC coding (+ pointer to local LLVM CLI) |
| `09_umc_cinema_aviation_gaming.py` | UMC domains |
| `10_openusd_airspace_fetch.py` | OpenUSD airspace USDA |
| `11_game_ingest_project_domains.py` | ingest/project per game |
| `12_domain_tour.py` | Full tour |

```bash
python3 examples/01_mcp_tools_list.py
python3 examples/03_openai_models_and_chat.py
python3 examples/10_openusd_airspace_fetch.py
```

## RealityPro player (UUM8D)

Static player under [`realitypro-player/`](realitypro-player/):

- Loads live USDA (`/language-game/airspace-lattice.usda`)
- Lattice preview via Three.js CDN (no vendored WASM)
- Games catalog → ingest / project / MCP tools / UMC coding

Open locally:

```bash
cd realitypro-player && python3 -m http.server 8765
# browse http://127.0.0.1:8765/?apex=https://affine.earth
```

Steward deploy to cells (private OS tree script, HTML/JS only):

```bash
# from AppleGaiaFTCL
bash cells/xcode/scripts/cell-deploy/deploy-realitypro-player.sh
# → https://affine.earth/language-game/realitypro/
```

## SDK modules

- `affine_earth_sdk.mcp` — JSON-RPC MCP
- `affine_earth_sdk.openai_v1` — models / chat / responses / api-keys
- `affine_earth_sdk.language_games` — inject, game-turn, ingest/project
- `affine_earth_sdk.umc` — cinema / aviation / gaming / coding
- `affine_earth_sdk.openusd` — USDA fetch + lightweight parse
- `affine_earth_sdk.seals` — genesis seals (port of `mcp-client.js`)

## Docs

- [docs/DOMAINS.md](docs/DOMAINS.md)
- [docs/MCP.md](docs/MCP.md)
- [docs/OPENAI_V1.md](docs/OPENAI_V1.md)
- [docs/OPENUSD_AND_REALITYPRO.md](docs/OPENUSD_AND_REALITYPRO.md)
- [docs/NO_BINARIES.md](docs/NO_BINARIES.md)

## LLVM

Local LLVM suite CLI remains the sibling package in this public repo:

```bash
cd ..   # affine.earth.public root
python3 -m llm_llvm_bench.cli.main llvm --help
```

Example `08` only drives the **coding** UUM8D / UMC membrane — it does not vendor `clang` or OS binaries.
