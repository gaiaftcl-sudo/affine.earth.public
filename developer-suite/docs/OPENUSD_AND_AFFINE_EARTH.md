# OpenUSD + Affine.Earth OpenUSD (live map / 3D state)

## Goal

**Affine.Earth OpenUSD** is the Affine.Earth OS **live map / 3D state** surface for OpenUSD / UUM8D. The ATC surface must read like a **Flightradar24-class live map** (dark basemap, yellow heading sprites, trackpad zoom/pan), not a static USDA dump or a Pixar toolchain demo. No vendored `libusd`.

Canonical URL:

```text
https://affine.earth/language-game/openusd/
```

## Live USDA

```bash
curl -sS https://affine.earth/language-game/airspace-atc-world.usda | head
curl -sS https://affine.earth/language-game/airspace-lattice.usda | head
```

Scenes live under `/language-game/*.usda`. Language-game ingest/project drives membrane ticks alongside live ADS-B tracks.

### ATC / airspace binding

ATC sector-flow uses game `aviation_atc` (ingest/project/context). Load **`/language-game/airspace-atc-world.usda`** in the OpenUSD player; aircraft come from `GET /language-invariant/adsb/tracks` (not authored timeSamples).

Full third-party recipe: [ATC_INGEST_PROJECT.md](ATC_INGEST_PROJECT.md) · example `examples/14_atc_ingest_project_openusd.py`.

## OpenUSD player

`openusd-player/` is a **binary-free** HTML/JS shell:

- Fetches USDA from the apex
- FR24-class orthographic map + Affine SVG sprites + skins
- Scroll / pinch zoom (smooth lerp) · click-drag / space-drag pan · double-click zoom
- Airport quick-zoom buttons
- DOM HUD (`#openusd-live-hud`): focus ICAO · `ac=` · `zoom=` · `liveRefresh=`

Deploy: `cells/xcode/scripts/cell-deploy/deploy-openusd-player.sh`

## Nav prove (Playwright)

```bash
cd developer-suite/docs/receipts/atc_airport_video_20260724
python3 capture_openusd_nav.py
# → OPENUSD_NAV_INTERACTION_PASS
```
