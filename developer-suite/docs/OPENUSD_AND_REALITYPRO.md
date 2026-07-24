# OpenUSD + RealityPro (live 3D video-like state)

## Goal

RealityPro is the Affine.Earth OS **live 3D state** surface for OpenUSD / UUM8D. It must read like a **video** (time-evolving scene / strobing projection), not a static USDA dump or a Pixar toolchain demo. No vendored `libusd`.

## Live USDA

```bash
curl -sS https://affine.earth/language-game/airspace-lattice.usda | head
# Developer-suite fixture with explicit timeSamples:
# fixtures/openusd/airspace-lattice-live.usda
```

Scenes live under `/language-game/*.usda`. Language-game ingest/project drives membrane ticks that pulse the lattice.

### ATC / airspace binding

ATC sector-flow uses game `aviation_atc` (ingest/project/context). There is **no** separate `atc.usda` on the apex (404 measured 2026-07-24). Project ATC clearances, then load **`/language-game/airspace-lattice.usda`** in RealityPro and select game `aviation_atc` so membrane ticks pulse the airspace lattice.

Full third-party recipe: [ATC_INGEST_PROJECT.md](ATC_INGEST_PROJECT.md) · example `examples/14_atc_ingest_project_openusd.py` · receipt [`receipts/atc_openusd_20260724/`](receipts/atc_openusd_20260724/).

## RealityPro player

`realitypro-player/` is a **binary-free** HTML/JS shell:

- Fetches USDA from the apex
- Parses `xformOp:translate.timeSamples` when present
- Renders a **live** lattice with Three.js (CDN): orbit + breath + emissive strobe
- On every ingest/project/MCP/UMC action, calls `applyMembraneTick()` → visible pulse
- Auto-strobe: project every 2.5s so the scene keeps evolving like a video
- DOM HUD (`#realitypro-live-hud`) exposes `data-strobe-tick`, `data-clock-ms`, `data-membrane-ticks` for CDP proof

NATS-shaped subjects (aligned with OS language-game):

- `gaiaftcl.reality.manifold.realitypro.apex`
- `gaiaftcl.game.[user_vqbit_hash].projection.[scf_hash]`

Deployed path:  
`https://affine.earth/language-game/realitypro/`

Local:

```bash
cd realitypro-player && python3 -m http.server 8765
open 'http://127.0.0.1:8765/?apex=https://affine.earth'
```

Steward deploy (private OS tree):

```bash
bash cells/xcode/scripts/cell-deploy/deploy-realitypro-player.sh
# Also refresh USDA via deploy-language-game-ui.sh when airspace-lattice.usda changes
```
