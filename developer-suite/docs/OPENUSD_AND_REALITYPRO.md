# OpenUSD + RealityPro player

## Live USDA

```bash
curl -sS https://affine.earth/language-game/airspace-lattice.usda | head
curl -sS -o /dev/null -w '%{http_code}\n' https://affine.earth/language-game/airspace.html
```

There is no `/openusd` REST verb — scenes are static USDA under `/language-game/` plus language-game ingest/project for domain seeds.

## RealityPro player

`realitypro-player/` is a **binary-free** HTML/JS shell:

- Fetches USDA from the apex
- Renders a lattice preview with Three.js (CDN)
- Drives UUM8D games (catalog, ingest, project, MCP tools, UMC coding)

Deployed path (after steward rsync):  
`https://affine.earth/language-game/realitypro/`

Local:

```bash
cd realitypro-player && python3 -m http.server 8765
open 'http://127.0.0.1:8765/?apex=https://affine.earth'
```
