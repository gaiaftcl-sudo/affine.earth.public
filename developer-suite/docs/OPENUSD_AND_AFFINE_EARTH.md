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
- **UUM8D manifold staging** — discrete zoom bands (not CSS bitmap scale):
  - `HEMISPHERE` zoom `[0, 0.42)` — planetary / hemisphere skin + thinned high-altitude flows
  - `REGIONAL` zoom `[0.42, 1.15)` — continent / FIR corridor
  - `METRO` zoom `[1.15, 3.60)` — TMA / metro
  - `AIRPORT_WALK` zoom `[3.60, 14]` — runway diagram + surface pan sense
- Live ADS-B LOD pegged to band (distance-to-focus + max tracks + altitude thin)
- Skin crossfade on band transition (`manifold-stage.js` + `assets/skins/map-*.css`)
- Scroll / pinch zoom (smooth lerp) · click-drag pan · `◎` hemisphere · `⌖` airport walk
- HUD: manifold band · zoom rational · `lod_ac=` · focus ICAO

Deploy: `cells/xcode/scripts/cell-deploy/deploy-openusd-player.sh`

Also: `solar-weather.js` (terminator + band weather LOD + honest NOAA status) and `traffic-warnings.js` (separation minima by band).

## Nav / manifold / wx prove (Playwright)

```bash
cd developer-suite/docs/receipts/atc_airport_video_20260724
python3 capture_openusd_nav.py
# → OPENUSD_NAV_INTERACTION_PASS
python3 capture_manifold_bands.py
# → OPENUSD_MANIFOLD_BANDS_PASS
python3 capture_wx_warnings.py
# → OPENUSD_WX_WARNINGS_PASS
python3 ../../tests/test_traffic_warnings_separation.py
# → TRAFFIC_WARNINGS_SEPARATION_PASS
```
