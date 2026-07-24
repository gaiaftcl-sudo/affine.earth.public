# No binaries doctrine

This `developer-suite/` is for **third-party developers**. It must stay free of Affine.Earth OS binaries.

## Never commit

- `GaiaFTCLCLI`, `.app`, `.dmg`, cell ISOs
- GGUF / GGML weights
- Mach-O / ELF / `.dylib` / `.so` / `.wasm` blobs
- Anything under `cells/xcode/Sources/` copied into this tree

## How examples run

Examples call the **live HTTPS apex** (`https://affine.earth` by default):

- MCP: `POST /language-invariant/mcp`
- OpenAI: `GET /v1/models`, `POST /v1/chat/completions`, `POST /v1/responses`
- Language games: inject, game-turn, UMC, game ingest/project
- OpenUSD: `GET /language-game/*.usda`

Local LLVM CLI demos point at the sibling package `llm_llvm_bench` in this public repo — they do **not** vendor a toolchain.

## Gate

```bash
python3 scripts/check_no_binaries.py
```

Must print `NO_BINARIES_PASS` before any commit to `affine.earth.public`.
